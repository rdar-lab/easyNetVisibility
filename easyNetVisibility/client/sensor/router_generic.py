"""
Generic router integration module using heuristic approach.

This module provides a generic integration for routers without specific API documentation.
It attempts to discover devices using common patterns found across various router interfaces:
- DHCP lease tables
- Connected device lists
- Common HTML parsing patterns

This is intended as a starting point that can be improved after testing with real devices.
"""

import logging
import warnings
import re

import requests

import network_utils

try:
    from urllib3.exceptions import InsecureRequestWarning
except ImportError:
    InsecureRequestWarning = None

_logger = logging.getLogger('EasyNetVisibility')

_router_host = None
_router_username = None
_router_password = None
_validate_ssl = True


def init(host, username, password, validate_ssl=True):
    """
    Initialize generic router connection parameters.

    Args:
        host: Router IP or hostname (e.g., 'http://192.168.1.1')
        username: Router admin username
        password: Router admin password
        validate_ssl: Whether to validate SSL certificates
    """
    global _router_host, _router_username, _router_password, _validate_ssl

    _router_host = host
    _router_username = username
    _router_password = password
    _validate_ssl = validate_ssl

    _logger.info(f"Generic router integration initialized for host: {host}")


def _make_request(endpoint, method='GET', data=None):
    """
    Make a request to router interface.

    Args:
        endpoint: Endpoint path
        method: HTTP method (GET or POST)
        data: Data for POST requests

    Returns:
        str: Response text from router
    """
    if not _router_host:
        raise ValueError("Router not initialized. Call init() first.")

    url = f"{_router_host}{endpoint}"

    try:
        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            if method == 'POST':
                response = requests.post(
                    url,
                    auth=(_router_username, _router_password),
                    data=data,
                    verify=_validate_ssl,
                    timeout=30
                )
            else:
                response = requests.get(
                    url,
                    auth=(_router_username, _router_password),
                    verify=_validate_ssl,
                    timeout=30
                )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error making Generic router request to {endpoint}: {e}")
        raise


def get_dhcp_leases():
    """
    Get DHCP leases from router using common endpoints.

    Attempts to retrieve DHCP lease information by trying multiple common endpoints
    and parsing patterns found across different router interfaces.

    Returns:
        list: List of DHCP lease entries with IP, MAC, and hostname information
    """
    try:
        _logger.info(f"Fetching DHCP leases from Generic router")

        leases = []

        # Try common DHCP status endpoints
        endpoints = [
            '/status.html',
            '/dhcp.html',
            '/dhcp_status.html',
            '/dhcp_clients.html',
            '/lan_dhcp.html',
            '/lan_dhcp_clients.html',
            '/status/dhcp.html',
            '/network/dhcp.html'
        ]

        for endpoint in endpoints:
            try:
                response_text = _make_request(endpoint)

                # Parse HTML to extract DHCP lease information
                # Try multiple common patterns

                # Pattern 1: Standard table format with hostname, MAC, IP
                lease_pattern = r'<tr[^>]*>.*?<td[^>]*>([^<]*)</td>.*?<td[^>]*>([0-9A-Fa-f:]+)</td>.*?<td[^>]*>(\d+\.\d+\.\d+\.\d+)</td>'
                matches = re.findall(lease_pattern, response_text, re.DOTALL)

                for match in matches:
                    hostname = match[0].strip()
                    mac = match[1].strip()
                    ip = match[2].strip()

                    if mac and ip:
                        leases.append({
                            'hostname': hostname if hostname and hostname not in ['-', '', 'N/A', 'Unknown'] else '',
                            'mac': mac,
                            'ip': ip
                        })

                # Pattern 2: Alternative table format (IP, MAC, hostname order)
                if not leases:
                    lease_pattern2 = r'<tr[^>]*>.*?<td[^>]*>(\d+\.\d+\.\d+\.\d+)</td>.*?<td[^>]*>([0-9A-Fa-f:]+)</td>.*?<td[^>]*>([^<]*)</td>'
                    matches2 = re.findall(lease_pattern2, response_text, re.DOTALL)

                    for match in matches2:
                        ip = match[0].strip()
                        mac = match[1].strip()
                        hostname = match[2].strip()

                        if mac and ip:
                            leases.append({
                                'hostname': hostname if hostname and hostname not in ['-', '', 'N/A', 'Unknown'] else '',
                                'mac': mac,
                                'ip': ip
                            })

                if leases:
                    break  # Found leases, stop trying endpoints

            except Exception as e:
                _logger.debug(f"Could not fetch from {endpoint}: {e}")
                continue

        _logger.info(f"Retrieved {len(leases)} DHCP leases from Generic router")
        return leases

    except Exception as e:
        _logger.error(f"Error fetching DHCP leases: {e}")
        return []


def get_connected_devices():
    """
    Get connected devices from router using common endpoints.

    Attempts to retrieve connected device information from common status pages
    by parsing HTML for IP and MAC address patterns.

    Returns:
        list: List of device entries with MAC and IP information
    """
    try:
        _logger.info(f"Fetching connected devices from Generic router")

        devices = []

        # Try common device status endpoints
        endpoints = [
            '/status.html',
            '/devices.html',
            '/connected_devices.html',
            '/lan_status.html',
            '/lan_clients.html',
            '/network/clients.html'
        ]

        for endpoint in endpoints:
            try:
                response_text = _make_request(endpoint)

                # Parse for device information
                # Pattern 1: IP followed by MAC
                device_pattern = r'(\d+\.\d+\.\d+\.\d+)[^0-9A-Fa-f]*([0-9A-Fa-f:]{17})'
                matches = re.findall(device_pattern, response_text)

                for match in matches:
                    ip = match[0].strip()
                    mac = match[1].strip()

                    if mac and ip:
                        devices.append({
                            'ip': ip,
                            'mac': mac
                        })

                # Pattern 2: MAC followed by IP (try reverse if no results)
                if not devices:
                    device_pattern2 = r'([0-9A-Fa-f:]{17})[^0-9]*(\d+\.\d+\.\d+\.\d+)'
                    matches2 = re.findall(device_pattern2, response_text)

                    for match in matches2:
                        mac = match[0].strip()
                        ip = match[1].strip()

                        if mac and ip:
                            devices.append({
                                'ip': ip,
                                'mac': mac
                            })

                if devices:
                    break  # Found devices, stop trying endpoints

            except Exception as e:
                _logger.debug(f"Could not fetch from {endpoint}: {e}")
                continue

        _logger.info(f"Retrieved {len(devices)} connected devices from Generic router")
        return devices

    except Exception as e:
        _logger.error(f"Error fetching connected devices: {e}")
        return []


def discover_devices():
    """
    Discover live devices from generic router.

    Uses multiple sources to identify active devices:
    1. DHCP leases - devices with active DHCP assignments
    2. Connected devices - devices shown in status pages

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info(f"Starting Generic router device discovery")

    devices = {}

    # Method 1: Get devices from DHCP leases
    dhcp_leases = get_dhcp_leases()
    if dhcp_leases:
        _logger.info(f"Retrieved {len(dhcp_leases)} DHCP leases from Generic router")
        for lease in dhcp_leases:
            ip = lease.get('ip', '')
            mac = lease.get('mac', '')
            hostname = lease.get('hostname', '')

            if ip and mac:
                mac_normalized = network_utils.convert_mac(mac)
                display_name = hostname if hostname else ip

                devices[mac_normalized] = {
                    'hostname': display_name,
                    'ip': ip,
                    'mac': mac_normalized,
                    'vendor': 'Unknown'
                }
    else:
        _logger.info(f"No DHCP leases returned from Generic router")

    # Method 2: Get connected devices
    connected_devices = get_connected_devices()
    if connected_devices:
        _logger.info(f"Retrieved {len(connected_devices)} connected devices from Generic router")
        for device in connected_devices:
            ip = device.get('ip', '')
            mac = device.get('mac', '')

            if ip and mac:
                mac_normalized = network_utils.convert_mac(mac)

                # Add if not already present from DHCP
                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': ip,  # Use IP as hostname if no DHCP info
                        'ip': ip,
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }
    else:
        _logger.info(f"No connected devices returned from Generic router")

    result_devices = list(devices.values())
    _logger.info(f"Generic router discovered {len(result_devices)} devices")

    return result_devices
