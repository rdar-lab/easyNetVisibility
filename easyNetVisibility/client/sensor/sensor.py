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
bezeq = None
partner = None

try:
    import fortigate as fortigate_module
    fortigate = fortigate_module
except ImportError:
    pass

try:
    import openwrt as openwrt_module
    openwrt = openwrt_module
except ImportError:
    pass

try:
    import ddwrt as ddwrt_module
    ddwrt = ddwrt_module
except ImportError:
    pass

try:
    import bezeq as bezeq_module
    bezeq = bezeq_module
except ImportError:
    pass

try:
    import partner as partner_module
    partner = partner_module
except ImportError:
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
                continue
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
                continue
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
                continue
        except Exception as e:
            _logger.exception("DD-WRT scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_bezeq_scan():
    """Scan Bezeq router for devices."""
    while 1:
        try:
            if bezeq:
                devices = bezeq.discover_devices()
                _logger.info(f"Bezeq detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("Bezeq module not available")
                continue
        except Exception as e:
            _logger.exception("Bezeq scan error: " + str(e))

        sleep(60 * 10)  # Scan every 10 minutes


def start_partner_scan():
    """Scan Partner Fiber router for devices."""
    while 1:
        try:
            if partner:
                devices = partner.discover_devices()
                _logger.info(f"Partner detected {len(devices)} devices")
                if len(devices) > 0:
                    server_api.add_devices(devices)
            else:
                _logger.warning("Partner module not available")
                continue
        except Exception as e:
            _logger.exception("Partner scan error: " + str(e))

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

                fortigate.init(fortigate_host, fortigate_api_key, validate_ssl)

                # Start Fortigate scanning thread
                fortigate_thread = threading.Thread(target=start_fortigate_scan)
                fortigate_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize Fortigate integration: {e}")
    elif fortigate_enabled and not fortigate:
        _logger.warning("Fortigate is enabled in config but module is not available")
    else:
        _logger.info("Fortigate integration is disabled")

    # Initialize OpenWRT if configured
    openwrt_enabled = False
    if config.has_section('OpenWRT') and config.has_option('OpenWRT', 'enabled'):
        openwrt_enabled_param = config.get('OpenWRT', 'enabled')
        openwrt_enabled = openwrt_enabled_param.lower() in ['true', '1', 'yes']

    if openwrt_enabled and openwrt:
        _logger.info("OpenWRT integration is enabled")

        if not config.has_option('OpenWRT', 'host'):
            _logger.error("OpenWRT enabled but 'host' option is missing in config")
        elif not config.has_option('OpenWRT', 'username'):
            _logger.error("OpenWRT enabled but 'username' option is missing in config")
        elif not config.has_option('OpenWRT', 'password'):
            _logger.error("OpenWRT enabled but 'password' option is missing in config")
        else:
            try:
                openwrt_host = config.get('OpenWRT', 'host')
                openwrt_username = config.get('OpenWRT', 'username')
                openwrt_password = config.get('OpenWRT', 'password')

                if config.has_option('OpenWRT', 'validateSSL'):
                    validate_ssl_param = config.get('OpenWRT', 'validateSSL')
                    validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
                else:
                    validate_ssl = True

                openwrt.init(openwrt_host, openwrt_username, openwrt_password, validate_ssl)

                openwrt_thread = threading.Thread(target=start_openwrt_scan)
                openwrt_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize OpenWRT integration: {e}")
    elif openwrt_enabled and not openwrt:
        _logger.warning("OpenWRT is enabled in config but module is not available")
    else:
        _logger.info("OpenWRT integration is disabled")

    # Initialize DD-WRT if configured
    ddwrt_enabled = False
    if config.has_section('DDWRT') and config.has_option('DDWRT', 'enabled'):
        ddwrt_enabled_param = config.get('DDWRT', 'enabled')
        ddwrt_enabled = ddwrt_enabled_param.lower() in ['true', '1', 'yes']

    if ddwrt_enabled and ddwrt:
        _logger.info("DD-WRT integration is enabled")

        if not config.has_option('DDWRT', 'host'):
            _logger.error("DD-WRT enabled but 'host' option is missing in config")
        elif not config.has_option('DDWRT', 'username'):
            _logger.error("DD-WRT enabled but 'username' option is missing in config")
        elif not config.has_option('DDWRT', 'password'):
            _logger.error("DD-WRT enabled but 'password' option is missing in config")
        else:
            try:
                ddwrt_host = config.get('DDWRT', 'host')
                ddwrt_username = config.get('DDWRT', 'username')
                ddwrt_password = config.get('DDWRT', 'password')

                if config.has_option('DDWRT', 'validateSSL'):
                    validate_ssl_param = config.get('DDWRT', 'validateSSL')
                    validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
                else:
                    validate_ssl = True

                ddwrt.init(ddwrt_host, ddwrt_username, ddwrt_password, validate_ssl)

                ddwrt_thread = threading.Thread(target=start_ddwrt_scan)
                ddwrt_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize DD-WRT integration: {e}")
    elif ddwrt_enabled and not ddwrt:
        _logger.warning("DD-WRT is enabled in config but module is not available")
    else:
        _logger.info("DD-WRT integration is disabled")

    # Initialize Bezeq if configured
    bezeq_enabled = False
    if config.has_section('Bezeq') and config.has_option('Bezeq', 'enabled'):
        bezeq_enabled_param = config.get('Bezeq', 'enabled')
        bezeq_enabled = bezeq_enabled_param.lower() in ['true', '1', 'yes']

    if bezeq_enabled and bezeq:
        _logger.info("Bezeq integration is enabled")

        if not config.has_option('Bezeq', 'host'):
            _logger.error("Bezeq enabled but 'host' option is missing in config")
        elif not config.has_option('Bezeq', 'username'):
            _logger.error("Bezeq enabled but 'username' option is missing in config")
        elif not config.has_option('Bezeq', 'password'):
            _logger.error("Bezeq enabled but 'password' option is missing in config")
        else:
            try:
                bezeq_host = config.get('Bezeq', 'host')
                bezeq_username = config.get('Bezeq', 'username')
                bezeq_password = config.get('Bezeq', 'password')

                if config.has_option('Bezeq', 'validateSSL'):
                    validate_ssl_param = config.get('Bezeq', 'validateSSL')
                    validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
                else:
                    validate_ssl = True

                bezeq.init(bezeq_host, bezeq_username, bezeq_password, validate_ssl)

                bezeq_thread = threading.Thread(target=start_bezeq_scan)
                bezeq_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize Bezeq integration: {e}")
    elif bezeq_enabled and not bezeq:
        _logger.warning("Bezeq is enabled in config but module is not available")
    else:
        _logger.info("Bezeq integration is disabled")

    # Initialize Partner if configured
    partner_enabled = False
    if config.has_section('Partner') and config.has_option('Partner', 'enabled'):
        partner_enabled_param = config.get('Partner', 'enabled')
        partner_enabled = partner_enabled_param.lower() in ['true', '1', 'yes']

    if partner_enabled and partner:
        _logger.info("Partner integration is enabled")

        if not config.has_option('Partner', 'host'):
            _logger.error("Partner enabled but 'host' option is missing in config")
        elif not config.has_option('Partner', 'username'):
            _logger.error("Partner enabled but 'username' option is missing in config")
        elif not config.has_option('Partner', 'password'):
            _logger.error("Partner enabled but 'password' option is missing in config")
        else:
            try:
                partner_host = config.get('Partner', 'host')
                partner_username = config.get('Partner', 'username')
                partner_password = config.get('Partner', 'password')

                if config.has_option('Partner', 'validateSSL'):
                    validate_ssl_param = config.get('Partner', 'validateSSL')
                    validate_ssl = validate_ssl_param.lower() not in ['false', '0', 'no']
                else:
                    validate_ssl = True

                partner.init(partner_host, partner_username, partner_password, validate_ssl)

                partner_thread = threading.Thread(target=start_partner_scan)
                partner_thread.start()
            except Exception as e:
                _logger.error(f"Failed to initialize Partner integration: {e}")
    elif partner_enabled and not partner:
        _logger.warning("Partner is enabled in config but module is not available")
    else:
        _logger.info("Partner integration is disabled")

    health_check_thread = threading.Thread(target=start_health_check)
    health_check_thread.start()
    ping_sweep_thread = threading.Thread(target=start_ping_sweep)
    ping_sweep_thread.start()
    port_scan_thread = threading.Thread(target=start_port_scan)
    port_scan_thread.start()


if __name__ == '__main__':
    run()
