from time import sleep

import configparser
import logging
import threading

import healthCheck
import logs
import network_utils
import nmap
import server_api

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

    health_check_thread = threading.Thread(target=start_health_check)
    health_check_thread.start()
    ping_sweep_thread = threading.Thread(target=start_ping_sweep)
    ping_sweep_thread.start()
    port_scan_thread = threading.Thread(target=start_port_scan)
    port_scan_thread.start()


if __name__ == '__main__':
    run()
