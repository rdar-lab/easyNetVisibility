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

_ddwrt_host = None
_ddwrt_username = None
_ddwrt_password = None
_validate_ssl = True


def init(host, username, password, validate_ssl=True):
    """
    Initialize DD-WRT connection parameters.

    Args:
        host: DD-WRT IP or hostname (e.g., 'http://192.168.1.1')
        username: DD-WRT admin username
        password: DD-WRT admin password
        validate_ssl: Whether to validate SSL certificates
    """
    global _ddwrt_host, _ddwrt_username, _ddwrt_password, _validate_ssl

    _ddwrt_host = host
    _ddwrt_username = username
    _ddwrt_password = password
    _validate_ssl = validate_ssl

    _logger.info(f"DD-WRT integration initialized for host: {host}")


def _make_request(endpoint):
    """
    Make a request to DD-WRT web interface.

    Args:
        endpoint: Endpoint path

    Returns:
        str: Response text from DD-WRT
    """
    if not _ddwrt_host:
        raise ValueError("DD-WRT not initialized. Call init() first.")

    url = f"{_ddwrt_host}{endpoint}"

    try:
        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            response = requests.get(
                url,
                auth=(_ddwrt_username, _ddwrt_password),
                verify=_validate_ssl,
                timeout=30
            )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error making DD-WRT request to {endpoint}: {e}")
        raise


def get_dhcp_leases():
    """
    Get DHCP leases from DD-WRT.

    Parses the DHCP status page to extract active leases.

    Returns:
        list: List of DHCP lease entries with IP, MAC, and hostname information
    """
    try:
        _logger.info("Fetching DHCP leases from DD-WRT")

        # DD-WRT DHCP status page
        response_text = _make_request('/Status_Lan.asp')

        leases = []

        # Parse HTML to extract DHCP lease information
        # DD-WRT typically shows leases in a table format
        # Look for patterns like: <td>hostname</td><td>MAC</td><td>IP</td><td>expires</td>

        # Extract lease table data using regex
        # Pattern matches table rows with lease information
        lease_pattern = r'<tr[^>]*>.*?<td[^>]*>([^<]+)</td>.*?<td[^>]*>([0-9A-Fa-f:]+)</td>.*?<td[^>]*>(\d+\.\d+\.\d+\.\d+)</td>'
        matches = re.findall(lease_pattern, response_text, re.DOTALL)

        for match in matches:
            hostname = match[0].strip()
            mac = match[1].strip()
            ip = match[2].strip()

            if mac and ip:
                leases.append({
                    'hostname': hostname if hostname and hostname != '-' else '',
                    'mac': mac,
                    'ip': ip
                })

        # Alternative: Try to parse from JavaScript variable if present
        if not leases:
            js_pattern = r'var\s+lease\s*=\s*"([^"]+)"'
            js_matches = re.findall(js_pattern, response_text)
            for js_lease in js_matches:
                # Format: hostname,MAC,IP,expires
                parts = js_lease.split(',')
                if len(parts) >= 3:
                    leases.append({
                        'hostname': parts[0] if parts[0] != '-' else '',
                        'mac': parts[1],
                        'ip': parts[2]
                    })

        _logger.info(f"Retrieved {len(leases)} DHCP leases from DD-WRT")
        return leases

    except Exception as e:
        _logger.error(f"Error fetching DHCP leases: {e}")
        return []


def get_wireless_clients():
    """
    Get wireless clients from DD-WRT.

    Parses the wireless status page for connected clients.

    Returns:
        list: List of wireless client entries with MAC and signal information
    """
    try:
        _logger.info("Fetching wireless clients from DD-WRT")

        # DD-WRT wireless status page
        response_text = _make_request('/Status_Wireless.asp')

        clients = []

        # Parse wireless client table
        # Look for MAC addresses in wireless client table
        wireless_pattern = r'<td[^>]*>([0-9A-Fa-f:]{17})</td>'
        matches = re.findall(wireless_pattern, response_text)

        for mac in matches:
            if mac:
                clients.append({
                    'mac': mac.strip()
                })

        _logger.info(f"Retrieved {len(clients)} wireless clients from DD-WRT")
        return clients

    except Exception as e:
        _logger.error(f"Error fetching wireless clients: {e}")
        return []


def discover_devices():
    """
    Discover live devices from DD-WRT router.

    Uses multiple sources to identify active devices:
    1. DHCP leases - devices with active DHCP assignments
    2. Wireless clients - devices connected to WiFi

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info("Starting DD-WRT device discovery")

    devices = {}

    # Method 1: Get devices from DHCP leases
    dhcp_leases = get_dhcp_leases()
    if dhcp_leases:
        _logger.info(f"Retrieved {len(dhcp_leases)} DHCP leases from DD-WRT")
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
        _logger.info("No DHCP leases returned from DD-WRT")

    # Method 2: Get wireless clients and enrich with existing data
    wireless_clients = get_wireless_clients()
    if wireless_clients:
        _logger.info(f"Retrieved {len(wireless_clients)} wireless clients from DD-WRT")
        for client in wireless_clients:
            mac = client.get('mac', '')
            if mac:
                mac_normalized = network_utils.convert_mac(mac)
                # If not already in devices, add with MAC only
                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': mac_normalized,
                        'ip': '',
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }
    else:
        _logger.info("No wireless clients returned from DD-WRT")

    result_devices = list(devices.values())
    _logger.info(f"DD-WRT discovered {len(result_devices)} devices")

    return result_devices
