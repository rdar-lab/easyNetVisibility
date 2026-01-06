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
_vdom = None


def init(host, api_key, validate_ssl=True, vdom=None):
    """
    Initialize Fortigate connection parameters.

    Args:
        host: Fortigate IP or hostname (e.g., 'https://192.168.1.1')
        api_key: Fortigate API key for authentication
        validate_ssl: Whether to validate SSL certificates
        vdom: Virtual Domain name (optional, defaults to None which means no VDOM parameter)
    """
    global _fortigate_host, _fortigate_api_key, _validate_ssl, _vdom

    _fortigate_host = host
    _fortigate_api_key = api_key
    _validate_ssl = validate_ssl
    _vdom = vdom

    if vdom:
        _logger.info(f"Fortigate integration initialized for host: {host}, VDOM: {vdom}")
    else:
        _logger.info(f"Fortigate integration initialized for host: {host} (no VDOM specified)")


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


def get_firewall_sessions():
    """
    Get active firewall sessions from Fortigate.

    This queries the firewall session table to identify devices with active traffic.
    Only live/active devices are returned.

    Returns:
        list: List of active session entries with IP and MAC information
    """
    try:
        _logger.info("Fetching firewall sessions from Fortigate")
        
        # Build endpoint with optional VDOM parameter
        if _vdom:
            endpoint = f'/api/v2/monitor/firewall/session?vdom={_vdom}&ip_version=ipv4&summary=true'
        else:
            endpoint = '/api/v2/monitor/firewall/session?ip_version=ipv4&summary=true'
        
        try:
            response = _make_api_request(endpoint)
            
            if response.get('status') == 'success':
                return response.get('results', [])
            else:
                _logger.warning(f"Fortigate firewall session request returned non-success status: {response}")
                return []
        except requests.exceptions.HTTPError as e:
            # Handle 424 Failed Dependency - typically means VDOM issue
            if e.response.status_code == 424:
                if _vdom:
                    _logger.warning(f"Fortigate returned 424 Failed Dependency with VDOM '{_vdom}'. "
                                  f"This may indicate the VDOM doesn't exist or API key lacks permission. "
                                  f"Retrying without VDOM parameter...")
                    # Retry without VDOM parameter
                    try:
                        endpoint_no_vdom = '/api/v2/monitor/firewall/session?ip_version=ipv4&summary=true'
                        response = _make_api_request(endpoint_no_vdom)
                        
                        if response.get('status') == 'success':
                            _logger.info("Successfully retrieved firewall sessions without VDOM parameter")
                            return response.get('results', [])
                        else:
                            _logger.warning(f"Fortigate firewall session request returned non-success status: {response}")
                            return []
                    except Exception as retry_error:
                        _logger.error(f"Retry without VDOM also failed: {retry_error}")
                        return []
                else:
                    _logger.error(f"Fortigate returned 424 Failed Dependency. "
                                f"Check your FortiGate configuration and API key permissions. Error: {e}")
                    return []
            else:
                # Log and return empty list for other HTTP errors
                _logger.error(f"HTTP error fetching firewall sessions: {e}")
                return []
    except Exception as e:
        _logger.error(f"Error fetching firewall sessions: {e}")
        return []


def get_dhcp_leases():
    """
    Get DHCP leases from Fortigate.

    This uses the correct DHCP select endpoint to retrieve active DHCP leases.

    Returns:
        list: List of DHCP lease entries with IP, MAC, and hostname information
    """
    try:
        _logger.info("Fetching DHCP leases from Fortigate")
        response = _make_api_request('/api/v2/monitor/system/dhcp/select')

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
    Discover live devices from Fortigate firewall.

    Uses two primary sources to identify active/live devices:
    1. DHCP leases - devices with active DHCP assignments
    2. Firewall sessions - devices with active traffic through the firewall

    This approach ensures only live devices are detected.

    Returns:
        list: List of device dictionaries with keys: hostname, ip, mac, vendor
    """
    _logger.info("Starting Fortigate device discovery")

    devices = {}

    # Method 1: Get devices from DHCP leases
    # DHCP leases represent devices that have recently requested an IP address
    dhcp_leases = get_dhcp_leases()
    if dhcp_leases:
        _logger.info(f"Retrieved {len(dhcp_leases)} DHCP leases from Fortigate")
        for lease in dhcp_leases:
            # DHCP lease fields may include: ip, mac, hostname, interface, etc.
            ip = lease.get('ip', '') or lease.get('ip-address', '')
            mac = lease.get('mac', '') or lease.get('mac-address', '')
            hostname = lease.get('hostname', '') or lease.get('host-name', '')

            if ip and mac:
                # Normalize MAC address using existing utility
                mac_normalized = network_utils.convert_mac(mac)

                # Use hostname if available, otherwise use IP
                display_name = hostname if hostname else ip

                devices[mac_normalized] = {
                    'hostname': display_name,
                    'ip': ip,
                    'mac': mac_normalized,
                    'vendor': 'Unknown'
                }
    else:
        _logger.info("No DHCP leases returned from Fortigate")

    # Method 2: Get devices from active firewall sessions
    # Firewall sessions represent devices with active network traffic
    firewall_sessions = get_firewall_sessions()
    if firewall_sessions:
        _logger.info(f"Retrieved {len(firewall_sessions)} firewall sessions from Fortigate")
        for session in firewall_sessions:
            # Session data structure varies; typically includes source/destination IPs
            # May include: src, dst, srcaddr, dstaddr, srcmac, etc.
            # We're interested in source devices (clients on the network)
            src_ip = session.get('src', '') or session.get('srcaddr', '') or session.get('source', '')
            src_mac = session.get('srcmac', '') or session.get('src_mac', '')

            # Also check destination for internal devices
            # Note: Destination MAC addresses are typically only available for internal-to-internal
            # traffic where the firewall has ARP knowledge of both endpoints. For external
            # destinations (internet), only the destination IP is available.
            dst_ip = session.get('dst', '') or session.get('dstaddr', '') or session.get('destination', '')
            dst_mac = session.get('dstmac', '') or session.get('dst_mac', '')

            # Process source device
            if src_ip and src_mac:
                mac_normalized = network_utils.convert_mac(src_mac)

                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': src_ip,  # Default to IP if no hostname
                        'ip': src_ip,
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }

            # Process destination device (for internal traffic)
            if dst_ip and dst_mac:
                mac_normalized = network_utils.convert_mac(dst_mac)

                if mac_normalized not in devices:
                    devices[mac_normalized] = {
                        'hostname': dst_ip,  # Default to IP if no hostname
                        'ip': dst_ip,
                        'mac': mac_normalized,
                        'vendor': 'Unknown'
                    }
    else:
        _logger.info("No firewall sessions returned from Fortigate")

    # Enrich firewall session devices with DHCP hostname information
    # This combines the best of both: live traffic detection + hostname resolution
    # Create a lookup map for efficient hostname enrichment
    dhcp_hostname_map = {}
    for lease in dhcp_leases:
        lease_mac = lease.get('mac', '') or lease.get('mac-address', '')
        if lease_mac:
            lease_mac_normalized = network_utils.convert_mac(lease_mac)
            hostname = lease.get('hostname', '') or lease.get('host-name', '')
            if hostname:
                dhcp_hostname_map[lease_mac_normalized] = hostname

    # Apply hostname enrichment using the lookup map
    for mac, device in devices.items():
        if device['hostname'] == device['ip'] and mac in dhcp_hostname_map:
            devices[mac]['hostname'] = dhcp_hostname_map[mac]

    result_devices = list(devices.values())
    _logger.info(f"Fortigate discovered {len(result_devices)} live devices")

    return result_devices
