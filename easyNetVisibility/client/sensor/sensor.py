import configparser
import logging
import threading
from time import sleep

import healthCheck
import logs
import network_utils
import nmap
import server_api

# Router integrations are optional
fortigate = None
openwrt = None
ddwrt = None
router_generic = None

try:
    import fortigate as fortigate_module
    fortigate = fortigate_module
except ImportError:
    pass

try:
    import openwrt as openwrt_module
    openwrt = openwrt_module
except ImportError:
    pass  # OpenWRT module is optional

try:
    import ddwrt as ddwrt_module
    ddwrt = ddwrt_module
except ImportError:
    pass  # DD-WRT module is optional

try:
    import router_generic as router_generic_module
    router_generic = router_generic_module
except ImportError:
    pass  # Generic router module is optional

logs.setup()
_logger = logging.getLogger('EasyNetVisibility')


def start_ping_sweep():
    while 1:
        try:
            devices = nmap.ping_sweep()
            _logger.info(f"Detected {len(devices)} devices")
            if len(devices) > 0:
                server_api.add_devices(devices)
        except Exception as e:
            _logger.exception("Ping sweep error: " + str(e))

        sleep(60 * 10)


def start_port_scan():
    while 1:
        # Port Scan Every Hour, sleeping first to let first ping sweep finish
        sleep(60)
        try:
            for ports in nmap.port_scan():
                _logger.info(f"Detected {len(ports)} open ports")
                if len(ports) > 0:
                    server_api.add_ports(ports)
        except Exception as e:
            _logger.exception("Port scan error: " + str(e))

        sleep(60 * 60)


def start_fortigate_scan():
    """Scan Fortigate firewall for devices."""
    while 1:
        try:
            if fortigate:
                devices = fortigate.discover_devices()
                _logger.info(f"Fortigate detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("Fortigate module not available")
        except Exception as e:
            _logger.exception("Fortigate scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_openwrt_scan():
    """Scan OpenWRT router for devices."""
    while 1:
        try:
            if openwrt:
                devices = openwrt.discover_devices()
                _logger.info(f"OpenWRT detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("OpenWRT module not available")
        except Exception as e:
            _logger.exception("OpenWRT scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_ddwrt_scan():
    """Scan DD-WRT router for devices."""
    while 1:
        try:
            if ddwrt:
                devices = ddwrt.discover_devices()
                _logger.info(f"DD-WRT detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("DD-WRT module not available")
        except Exception as e:
            _logger.exception("DD-WRT scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_generic_router_scan():
    """Scan generic router for devices."""
    while 1:
        try:
            if router_generic:
                devices = router_generic.discover_devices()
                _logger.info(f"Generic Router detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("Generic router module not available")
        except Exception as e:
            _logger.exception(f"Generic Router scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_health_check():
    while 1:
        try:
            # report health
            healthCheck.report_health()
        except Exception as e:
            _logger.exception("Health check error: " + str(e))

        sleep(60 * 5)


def _initialize_router_integration(config, section_name, router_module, scan_function, 
                                    auth_type='username_password', router_display_name=None):
    """
    Helper function to initialize router integrations with consistent logic.
    
    Args:
        config: ConfigParser object with configuration
        section_name: Name of the config section (e.g., 'OpenWRT', 'DDWRT')
        router_module: The imported router module (e.g., openwrt, ddwrt)
        scan_function: The scan function to run in a thread
        auth_type: 'api_key' for Fortigate, 'username_password' for others
        router_display_name: Display name for logging (defaults to section_name)
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    if router_display_name is None:
        router_display_name = section_name
    
    # Check if enabled
    enabled = False
    if config.has_section(section_name) and config.has_option(section_name, 'enabled'):
        enabled_param = config.get(section_name, 'enabled')
        enabled = enabled_param.lower() in ['true', '1', 'yes']
    
    if not enabled:
        _logger.info(f"{router_display_name} integration is disabled")
        return False
    
    if not router_module:
        _logger.warning(f"{router_display_name} is enabled in config but module is not available")
        return False
    
    _logger.info(f"{router_display_name} integration is enabled")
    
    # Validate required options based on auth type
    if auth_type == 'api_key':
        required_options = ['host', 'apiKey']
    elif auth_type == 'username_password':
        required_options = ['host', 'username', 'password']
    else:
        _logger.error(f"Unknown auth_type: {auth_type}")
        return False
    
    # Check all required options exist
    for option in required_options:
        if not config.has_option(section_name, option):
            _logger.error(f"{router_display_name} enabled but '{option}' option is missing in config")
            return False
    
    # Initialize the router module
    try:
        # Get validateSSL option (common to all)
        validate_ssl = True
        if config.has_option(section_name, 'validateSSL'):
            validate_ssl_param = config.get(section_name, 'validateSSL')
            validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
        
        # Initialize based on auth type
        if auth_type == 'api_key':
            host = config.get(section_name, 'host')
            api_key = config.get(section_name, 'apiKey')
            router_module.init(host, api_key, validate_ssl)
        elif auth_type == 'username_password':
            host = config.get(section_name, 'host')
            username = config.get(section_name, 'username')
            password = config.get(section_name, 'password')
            router_module.init(host, username, password, validate_ssl)
        
        # Start scanning thread
        scan_thread = threading.Thread(target=scan_function)
        scan_thread.start()
        
        _logger.info(f"{router_display_name} integration initialized successfully")
        return True
        
    except Exception as e:
        _logger.error(f"Failed to initialize {router_display_name} integration: {e}")
        return False


def run():
    _logger.info('Starting up EasyNetVisibility Sensor')

    config = configparser.RawConfigParser()
    isOK = config.read(filenames='/opt/sensor/config/config.ini')
    if not isOK:
        _logger.error("Was unable to read the configuration file - /opt/sensor/config/config.ini is missing")
        return

    server_url = config.get('ServerAPI', 'serverURL')
    server_username = config.get('ServerAPI', 'serverUsername')
    server_password = config.get('ServerAPI', 'serverPassword')

    if config.has_option('ServerAPI', 'validateServerIdentity'):
        validate_server_identity_param = config.get('ServerAPI', 'validateServerIdentity')
        validate_server_identity = validate_server_identity_param != 'False'
    else:
        validate_server_identity = True

    if config.has_option('ServerAPI', 'callTimeout'):
        call_timeout_param = config.get('ServerAPI', 'callTimeout')
        call_timeout = int(call_timeout_param)
    else:
        call_timeout = 10000

    server_api.init(server_url, server_username, server_password, validate_server_identity, call_timeout)

    interface = config.get('General', 'interface')
    network_utils.init(interface)

    # Initialize router integrations using helper function
    _initialize_router_integration(config, 'Fortigate', fortigate, start_fortigate_scan, auth_type='api_key')
    _initialize_router_integration(config, 'OpenWRT', openwrt, start_openwrt_scan, auth_type='username_password')
    _initialize_router_integration(config, 'DDWRT', ddwrt, start_ddwrt_scan, auth_type='username_password', router_display_name='DD-WRT')
    _initialize_router_integration(config, 'GenericRouter', router_generic, start_generic_router_scan, auth_type='username_password', router_display_name='Generic Router')

    health_check_thread = threading.Thread(target=start_health_check)
    health_check_thread.start()
    ping_sweep_thread = threading.Thread(target=start_ping_sweep)
    ping_sweep_thread.start()
    port_scan_thread = threading.Thread(target=start_port_scan)
    port_scan_thread.start()


if __name__ == '__main__':
    run()
