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

_bezeq_host = None
_bezeq_username = None
_bezeq_password = None
_validate_ssl = True


def init(host, username, password, validate_ssl=True):
    """
    Initialize Bezeq Be router connection parameters.

    Args:
        host: Bezeq router IP or hostname (e.g., 'http://192.168.1.1')
        username: Bezeq router admin username
        password: Bezeq router admin password
        validate_ssl: Whether to validate SSL certificates
    """
    global _bezeq_host, _bezeq_username, _bezeq_password, _validate_ssl

    _bezeq_host = host
    _bezeq_username = username
    _bezeq_password = password
    _validate_ssl = validate_ssl

    _logger.info(f"Bezeq router integration initialized for host: {host}")


def _make_request(endpoint, method='GET', data=None):
    """
    Make a request to Bezeq router interface.

    Args:
        endpoint: Endpoint path
        method: HTTP method (GET or POST)
        data: Data for POST requests

    Returns:
        str: Response text from router
    """
    if not _bezeq_host:
        raise ValueError("Bezeq router not initialized. Call init() first.")

    url = f"{_bezeq_host}{endpoint}"

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
                    auth=(_bezeq_username, _bezeq_password),
                    data=data,
                    verify=_validate_ssl,
                    timeout=30
                )
            else:
                response = requests.get(
                    url,
                    auth=(_bezeq_username, _bezeq_password),
                    verify=_validate_ssl,
                    timeout=30
                )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error making Bezeq router request to {endpoint}: {e}")
        raise


def get_dhcp_leases():
    """
    Get DHCP leases from Bezeq router.

    Attempts to retrieve DHCP lease information using common endpoints.

    Returns:
        list: List of DHCP lease entries with IP, MAC, and hostname information
    """
    try:
        _logger.info("Fetching DHCP leases from Bezeq router")

        leases = []
        
        # Try common DHCP status endpoints
        endpoints = [
            '/status.html',
            '/dhcp.html',
            '/dhcp_status.html',
            '/lan_dhcp.html',
            '/status/dhcp.html'
        ]

        for endpoint in endpoints:
            try:
                response_text = _make_request(endpoint)
                
                # Parse HTML to extract DHCP lease information
                # Look for MAC addresses and IP addresses in table format
                
                # Pattern 1: Standard table format
                lease_pattern = r'<tr[^>]*>.*?<td[^>]*>([^<]*)</td>.*?<td[^>]*>([0-9A-Fa-f:]+)</td>.*?<td[^>]*>(\d+\.\d+\.\d+\.\d+)</td>'
                matches = re.findall(lease_pattern, response_text, re.DOTALL)
                
                for match in matches:
                    hostname = match[0].strip()
                    mac = match[1].strip()
                    ip = match[2].strip()
                    
                    if mac and ip:
                        leases.append({
                            'hostname': hostname if hostname and hostname not in ['-', '', 'N/A'] else '',
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
                                'hostname': hostname if hostname and hostname not in ['-', '', 'N/A'] else '',
                                'mac': mac,
                                'ip': ip
                            })
                
                if leases:
                    break  # Found leases, stop trying endpoints
                    
            except Exception as e:
                _logger.debug(f"Could not fetch from {endpoint}: {e}")
                continue

        _logger.info(f"Retrieved {len(leases)} DHCP leases from Bezeq router")
        return leases

    except Exception as e:
        _logger.error(f"Error fetching DHCP leases: {e}")
        return []


def get_connected_devices():
    """
    Get connected devices from Bezeq router.

    Attempts to retrieve connected device information from common status pages.

    Returns:
        list: List of device entries with MAC and IP information
    """
    try:
        _logger.info("Fetching connected devices from Bezeq router")

        devices = []
        
        # Try common device status endpoints
        endpoints = [
            '/status.html',
            '/devices.html',
            '/connected_devices.html',
            '/lan_status.html'
        ]

        for endpoint in endpoints:
            try:
                response_text = _make_request(endpoint)
                
                # Parse for device information
                # Look for MAC and IP patterns
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
                
                if devices:
                    break  # Found devices, stop trying endpoints
                    
            except Exception as e:
                _logger.debug(f"Could not fetch from {endpoint}: {e}")
                continue

        _logger.info(f"Retrieved {len(devices)} connected devices from Bezeq router")
        return devices

    except Exception as e:
        _logger.error(f"Error fetching connected devices: {e}")
        return []


def discover_devices():
    """
    Discover live devices from Bezeq Be router.

    Uses multiple sources to identify active devices:
    1. DHCP leases - devices with active DHCP assignments
    2. Connected devices - devices shown in status pages

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info("Starting Bezeq router device discovery")

    devices = {}

    # Method 1: Get devices from DHCP leases
    dhcp_leases = get_dhcp_leases()
    if dhcp_leases:
        _logger.info(f"Retrieved {len(dhcp_leases)} DHCP leases from Bezeq router")
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
        _logger.info("No DHCP leases returned from Bezeq router")

    # Method 2: Get connected devices
    connected_devices = get_connected_devices()
    if connected_devices:
        _logger.info(f"Retrieved {len(connected_devices)} connected devices from Bezeq router")
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
        _logger.info("No connected devices returned from Bezeq router")

    result_devices = list(devices.values())
    _logger.info(f"Bezeq router discovered {len(result_devices)} devices")

    return result_devices
