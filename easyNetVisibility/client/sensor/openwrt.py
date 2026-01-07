import logging
import warnings

import requests

import network_utils

try:
    from urllib3.exceptions import InsecureRequestWarning
except ImportError:
    InsecureRequestWarning = None

_logger = logging.getLogger('EasyNetVisibility')

_openwrt_host = None
_openwrt_username = None
_openwrt_password = None
_validate_ssl = True


def init(host, username, password, validate_ssl=True):
    """
    Initialize OpenWRT connection parameters.

    Args:
        host: OpenWRT IP or hostname (e.g., 'http://192.168.1.1')
        username: OpenWRT admin username
        password: OpenWRT admin password
        validate_ssl: Whether to validate SSL certificates
    """
    global _openwrt_host, _openwrt_username, _openwrt_password, _validate_ssl

    _openwrt_host = host
    _openwrt_username = username
    _openwrt_password = password
    _validate_ssl = validate_ssl

    _logger.info(f"OpenWRT integration initialized for host: {host}")


def _make_uci_request(command):
    """
    Make a UCI (Unified Configuration Interface) request to OpenWRT.

    Args:
        command: UCI command to execute

    Returns:
        str: Response from OpenWRT
    """
    if not _openwrt_host:
        raise ValueError("OpenWRT not initialized. Call init() first.")

    url = f"{_openwrt_host}/cgi-bin/luci/admin/uci"

    try:
        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            response = requests.post(
                url,
                auth=(_openwrt_username, _openwrt_password),
                data={'command': command},
                verify=_validate_ssl,
                timeout=30
            )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error making OpenWRT UCI request: {e}")
        raise


def _make_api_request(endpoint):
    """
    Make an API request to OpenWRT using RPC.

    Args:
        endpoint: API endpoint path

    Returns:
        dict: JSON response from OpenWRT
    """
    if not _openwrt_host:
        raise ValueError("OpenWRT not initialized. Call init() first.")

    url = f"{_openwrt_host}/cgi-bin/luci/rpc{endpoint}"

    try:
        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            response = requests.get(
                url,
                auth=(_openwrt_username, _openwrt_password),
                verify=_validate_ssl,
                timeout=30
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error making OpenWRT API request to {endpoint}: {e}")
        raise


def get_dhcp_leases():
    """
    Get DHCP leases from OpenWRT.

    Reads the DHCP leases file which contains active DHCP assignments.

    Returns:
        list: List of DHCP lease entries with IP, MAC, and hostname information
    """
    try:
        _logger.info("Fetching DHCP leases from OpenWRT")

        # OpenWRT stores DHCP leases in /tmp/dhcp.leases
        # Format: <expiry> <MAC> <IP> <hostname> <client-id>
        url = f"{_openwrt_host}/cgi-bin/luci/admin/status/dhcpleases"

        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            response = requests.get(
                url,
                auth=(_openwrt_username, _openwrt_password),
                verify=_validate_ssl,
                timeout=30
            )

        if response.status_code == 200:
            leases = []
            try:
                data = response.json()
                if isinstance(data, dict) and 'dhcp_leases' in data:
                    for lease in data['dhcp_leases']:
                        leases.append({
                            'ip': lease.get('ipaddr', ''),
                            'mac': lease.get('macaddr', ''),
                            'hostname': lease.get('hostname', '')
                        })
                elif isinstance(data, list):
                    for lease in data:
                        leases.append({
                            'ip': lease.get('ipaddr', lease.get('ip', '')),
                            'mac': lease.get('macaddr', lease.get('mac', '')),
                            'hostname': lease.get('hostname', lease.get('name', ''))
                        })
            except Exception as e:
                _logger.debug(f"Could not parse JSON response, trying text format: {e}")
                # Try parsing text format: <expiry> <MAC> <IP> <hostname> <client-id>
                for line in response.text.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 4:
                            leases.append({
                                'mac': parts[1],
                                'ip': parts[2],
                                'hostname': parts[3] if parts[3] != '*' else ''
                            })

            _logger.info(f"Retrieved {len(leases)} DHCP leases from OpenWRT")
            return leases
        else:
            _logger.warning(f"OpenWRT DHCP request returned status {response.status_code}")
            return []
    except Exception as e:
        _logger.error(f"Error fetching DHCP leases: {e}")
        return []


def get_wireless_clients():
    """
    Get wireless clients from OpenWRT.

    Queries the wireless interface status for connected clients.

    Returns:
        list: List of wireless client entries with MAC information
    """
    try:
        _logger.info("Fetching wireless clients from OpenWRT")

        url = f"{_openwrt_host}/cgi-bin/luci/admin/status/wireless"

        with warnings.catch_warnings():
            if not _validate_ssl:
                if InsecureRequestWarning:
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                else:
                    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            response = requests.get(
                url,
                auth=(_openwrt_username, _openwrt_password),
                verify=_validate_ssl,
                timeout=30
            )

        if response.status_code == 200:
            clients = []
            try:
                data = response.json()
                # Parse wireless client data structure
                if isinstance(data, dict):
                    for iface, iface_data in data.items():
                        if isinstance(iface_data, dict) and 'assoclist' in iface_data:
                            for mac, client_data in iface_data['assoclist'].items():
                                clients.append({
                                    'mac': mac,
                                    'signal': client_data.get('signal', 0)
                                })
            except Exception as e:
                _logger.debug(f"Could not parse wireless clients response: {e}")

            _logger.info(f"Retrieved {len(clients)} wireless clients from OpenWRT")
            return clients
        else:
            _logger.warning(f"OpenWRT wireless clients request returned status {response.status_code}")
            return []
    except Exception as e:
        _logger.error(f"Error fetching wireless clients: {e}")
        return []


def discover_devices():
    """
    Discover live devices from OpenWRT router.

    Uses two primary sources to identify active devices:
    1. DHCP leases - devices with active DHCP assignments
    2. Wireless clients - devices connected to WiFi

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info("Starting OpenWRT device discovery")

    devices = {}

    # Method 1: Get devices from DHCP leases
    dhcp_leases = get_dhcp_leases()
    if dhcp_leases:
        _logger.info(f"Retrieved {len(dhcp_leases)} DHCP leases from OpenWRT")
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
        _logger.info("No DHCP leases returned from OpenWRT")

    # Method 2: Get wireless clients and enrich with DHCP data
    wireless_clients = get_wireless_clients()
    if wireless_clients:
        _logger.info(f"Retrieved {len(wireless_clients)} wireless clients from OpenWRT")
        for client in wireless_clients:
            mac = client.get('mac', '')
            if mac:
                mac_normalized = network_utils.convert_mac(mac)
                # If not already in devices from DHCP, add with MAC as identifier
                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': mac_normalized,  # Use MAC as hostname if no other info
                        'ip': '',  # No IP info from wireless list
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }
    else:
        _logger.info("No wireless clients returned from OpenWRT")

    result_devices = list(devices.values())
    _logger.info(f"OpenWRT discovered {len(result_devices)} devices")

    return result_devices
