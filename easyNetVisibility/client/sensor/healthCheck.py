import logging

import network_utils
import server_api


def report_health():
    logger = logging.getLogger('EasyNetVisibility')
    logger.info('Reporting health')

    health_info = {'mac': network_utils.get_mac(),
                   'hostname': network_utils.get_hostname()}

    server_api.report_sensor_health(health_info)
