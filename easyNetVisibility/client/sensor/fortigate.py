import logging
import warnings

import requests

import network_utils

try:
    from urllib3.exceptions import InsecureRequestWarning
except ImportError:
    # Fallback for older urllib3 versions
    InsecureRequestWarning = None

_logger = logging.getLogger('EasyNetVisibility')

_fortigate_host = None
_fortigate_api_key = None
_validate_ssl = True


def init(host, api_key, validate_ssl=True):
    """
    Initialize Fortigate connection parameters.

    Args:
        host: Fortigate IP or hostname (e.g., 'https://192.168.1.1')
        api_key: Fortigate API key for authentication
        validate_ssl: Whether to validate SSL certificates
    """
    global _fortigate_host, _fortigate_api_key, _validate_ssl

    _fortigate_host = host
    _fortigate_api_key = api_key
    _validate_ssl = validate_ssl

    _logger.info(f"Fortigate integration initialized for host: {host}")


def _make_api_request(endpoint):
    """
    Make an API request to Fortigate.

    Args:
        endpoint: API endpoint path (e.g., '/api/v2/monitor/system/arp')

    Returns:
        dict: JSON response from Fortigate
    """
    if not _fortigate_host:
        raise ValueError("Fortigate not initialized. Call init() first.")

    url = f"{_fortigate_host}{endpoint}"

    try:
        # Suppress SSL warnings only for this request if SSL validation is disabled
        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            # Use API key authentication via Authorization header
            headers = {
                'Authorization': f'Bearer {_fortigate_api_key}'
            }

            response = requests.get(
                url,
                headers=headers,
                verify=_validate_ssl,
                timeout=30
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log only the endpoint to avoid exposing credentials in URL
        _logger.error(f"Error making Fortigate API request to endpoint {endpoint}: {e}")
        raise


def get_user_devices():
    """
    Get user devices from Fortigate's built-in Assets view.

    This uses the FortiGate user device endpoint which provides comprehensive
    device information including hostname, IP, MAC, OS, and more.

    Returns:
        list: List of device entries from FortiGate's device database
    """
    try:
        _logger.info("Fetching user devices from Fortigate")
        response = _make_api_request('/api/v2/monitor/user/device')

        if response.get('status') == 'success':
            return response.get('results', [])
        else:
            _logger.warning(f"Fortigate user device request returned non-success status: {response}")
            return []
    except Exception as e:
        _logger.error(f"Error fetching user devices: {e}")
        return []


def get_arp_table():
    """
    Get ARP table from Fortigate (fallback method).

    Returns:
        list: List of ARP entries with IP and MAC addresses
    """
    try:
        _logger.info("Fetching ARP table from Fortigate")
        response = _make_api_request('/api/v2/monitor/system/arp')

        if response.get('status') == 'success':
            return response.get('results', [])
        else:
            _logger.warning(f"Fortigate ARP request returned non-success status: {response}")
            return []
    except Exception as e:
        _logger.error(f"Error fetching ARP table: {e}")
        return []


def get_dhcp_leases():
    """
    Get DHCP leases from Fortigate.

    Returns:
        list: List of DHCP lease entries
    """
    try:
        _logger.info("Fetching DHCP leases from Fortigate")
        response = _make_api_request('/api/v2/monitor/system/dhcp')

        if response.get('status') == 'success':
            return response.get('results', [])
        else:
            _logger.warning(f"Fortigate DHCP request returned non-success status: {response}")
            return []
    except Exception as e:
        _logger.error(f"Error fetching DHCP leases: {e}")
        return []


def discover_devices():
    """
    Discover devices from Fortigate firewall.

    Uses FortiGate's built-in user device database (Assets view) which provides
    comprehensive device information. Falls back to ARP table if device API fails.

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info("Starting Fortigate device discovery")

    devices = {}

    # Try to get devices from FortiGate's user device database (Assets view)
    # This is more efficient and provides richer information
    user_devices = get_user_devices()

    if user_devices:
        _logger.info(f"Retrieved {len(user_devices)} devices from FortiGate Assets")
        for device in user_devices:
            # FortiGate device API provides multiple fields
            # Common fields: mac_addr, ipv4_address, hostname, host_name, os_name, etc.
            mac = device.get('mac_addr', '') or device.get('mac', '')
            ip = device.get('ipv4_address', '') or device.get('ip', '')
            hostname = device.get('hostname', '') or device.get('host_name', '')
            os_name = device.get('os_name', '')

            if ip and mac:
                # Normalize MAC address using existing utility
                mac_normalized = network_utils.convert_mac(mac)

                # Use hostname if available, otherwise use IP
                display_name = hostname if hostname else ip

                # Use OS name as vendor if available
                vendor = os_name if os_name else 'Unknown'

                devices[mac_normalized] = {
                    'hostname': display_name,
                    'ip': ip,
                    'mac': mac_normalized,
                    'vendor': vendor
                }
    else:
        # Fallback to ARP table if user device API doesn't return results
        _logger.info("User device API returned no results, falling back to ARP table")
        arp_entries = get_arp_table()
        for entry in arp_entries:
            ip = entry.get('ip', '')
            mac = entry.get('mac', '')

            if ip and mac:
                # Normalize MAC address using existing utility
                mac_normalized = network_utils.convert_mac(mac)

                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': ip,  # Default to IP if no hostname
                        'ip': ip,
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }

        # Try to enrich with DHCP lease information for hostnames
        dhcp_leases = get_dhcp_leases()
        for lease in dhcp_leases:
            ip = lease.get('ip', '')
            mac = lease.get('mac', '')
            hostname = lease.get('hostname', '')

            if ip and mac:
                mac_normalized = network_utils.convert_mac(mac)

                if mac_normalized in devices:
                    # Update existing entry with hostname if available
                    if hostname:
                        devices[mac_normalized]['hostname'] = hostname
                else:
                    # Add new entry from DHCP
                    devices[mac_normalized] = {
                        'hostname': hostname if hostname else ip,
                        'ip': ip,
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }

    result_devices = list(devices.values())
    _logger.info(f"Fortigate discovered {len(result_devices)} devices")

    return result_devices
