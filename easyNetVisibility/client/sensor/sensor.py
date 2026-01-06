import configparser
import logging
import threading
from time import sleep

import healthCheck
import logs
import network_utils
import nmap
import server_api

# Fortigate integration is optional
fortigate = None
try:
    import fortigate as fortigate_module

    fortigate = fortigate_module
except ImportError:
    # Fortigate module is not installed; proceed without Fortigate integration
    pass

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
                # Continue to periodically log warning if module becomes unavailable
                continue
        except Exception as e:
            _logger.exception("Fortigate scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_health_check():
    while 1:
        try:
            # report health
            healthCheck.report_health()
        except Exception as e:
            _logger.exception("Health check error: " + str(e))

        sleep(60 * 5)


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

    # Initialize Fortigate if configured
    fortigate_enabled = False
    if config.has_section('Fortigate') and config.has_option('Fortigate', 'enabled'):
        fortigate_enabled_param = config.get('Fortigate', 'enabled')
        fortigate_enabled = fortigate_enabled_param.lower() in ['true', '1', 'yes']

    if fortigate_enabled and fortigate:
        _logger.info("Fortigate integration is enabled")

        # Check for required configuration options
        if not config.has_option('Fortigate', 'host'):
            _logger.error("Fortigate enabled but 'host' option is missing in config")
        elif not config.has_option('Fortigate', 'apiKey'):
            _logger.error("Fortigate enabled but 'apiKey' option is missing in config")
        else:
            try:
                fortigate_host = config.get('Fortigate', 'host')
                fortigate_api_key = config.get('Fortigate', 'apiKey')

                if config.has_option('Fortigate', 'validateSSL'):
                    validate_ssl_param = config.get('Fortigate', 'validateSSL')
                    validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
                else:
                    validate_ssl = True

                # Get optional VDOM parameter, default to 'root'
                vdom = 'root'
                if config.has_option('Fortigate', 'vdom'):
                    vdom_config = config.get('Fortigate', 'vdom')
                    # Use configured value if not empty
                    if vdom_config:
                        vdom = vdom_config

                fortigate.init(fortigate_host, fortigate_api_key, validate_ssl, vdom)

                # Start Fortigate scanning thread
                fortigate_thread = threading.Thread(target=start_fortigate_scan)
                fortigate_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize Fortigate integration: {e}")
    elif fortigate_enabled and not fortigate:
        _logger.warning("Fortigate is enabled in config but module is not available")
    else:
        _logger.info("Fortigate integration is disabled")

    health_check_thread = threading.Thread(target=start_health_check)
    health_check_thread.start()
    ping_sweep_thread = threading.Thread(target=start_ping_sweep)
    ping_sweep_thread.start()
    port_scan_thread = threading.Thread(target=start_port_scan)
    port_scan_thread.start()


if __name__ == '__main__':
    run()
