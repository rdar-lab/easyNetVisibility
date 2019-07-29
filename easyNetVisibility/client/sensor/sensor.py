from time import sleep

import ConfigParser
import logging
import threading

import healthCheck
import logs
import network_utils
import nmap
import server_api

logs.setup()
logger = logging.getLogger('EasyNetVisibility')


def start_ping_sweep():
    while 1:
        try:
            nmap.ping_sweep()
        except Exception, e:
            logger.error(str(e))
            pass

        sleep(20)


def start_port_scan():
    while 1:
        # Port Scan Every Hour, sleeping first to let first ping sweep finish
        sleep(60)
        try:
            nmap.port_scan()
        except Exception, e:
            logger.error(str(e))
            pass

        sleep(3540)


def start_health_check():
    while 1:
        try:
            # report health
            healthCheck.report_health()
        except Exception, e:
            logger.error(str(e))
            pass
        sleep(300)


def run():
    logger.info('Starting up EasyNetVisibility Sensor')

    config = ConfigParser.RawConfigParser()
    isOK = config.read(filenames='/opt/sensor/config/config.ini')
    if not isOK:
        logger.error("Was unable to read the configuration file - /opt/sensor/config/config.ini is missing")
        return

    server_url = config.get('ServerAPI', 'serverURL')
    server_username = config.get('ServerAPI', 'serverUsername')
    server_password = config.get('ServerAPI', 'serverPassword')
    validate_server_identity_param = config.get('ServerAPI', 'validateServerIdentity')
    validate_server_identity = True
    if validate_server_identity_param == 'False':
        validate_server_identity = False

    server_api.init(server_url, server_username, server_password, validate_server_identity)

    interface = config.get('General', 'interface')
    network_utils.init(interface)

    health_check_thread = threading.Thread(target=start_health_check)
    health_check_thread.start()
    ping_sweep_thread = threading.Thread(target=start_ping_sweep)
    ping_sweep_thread.start()
    port_scan_thread = threading.Thread(target=start_port_scan)
    port_scan_thread.start()


run()
