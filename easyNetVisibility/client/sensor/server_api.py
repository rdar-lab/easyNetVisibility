import logging

import requests

_server_api_address = ''
_server_username = None
_server_password = None
_validate_server_identity = False
_call_timeout = None

logger = logging.getLogger('EasyNetVisibility')


def init(param_server_api_address, param_server_username, param_server_password, param_validate_server_identity,
         param_call_timeout):
    global _server_api_address
    global _server_username
    global _server_password
    global _validate_server_identity
    global _call_timeout

    _server_api_address = param_server_api_address
    if param_server_username is not None and len(param_server_username) > 0:
        logger.info("Server authentication enabled")
        _server_username = param_server_username
        _server_password = param_server_password
    else:
        logger.info("Server authentication disabled")

    _validate_server_identity = param_validate_server_identity
    _call_timeout = param_call_timeout
    logger.info("Server connection set for server:" + _server_api_address)


def generate_session():
    session = requests.Session()
    if _server_username is not None:
        session.auth = (_server_username, _server_password)
    return session


def get_csrf_token(session):
    logger.info("Obtaining CSRF token")
    response_code, response = get('/api/csrf')
    if response_code != 200:
        raise Exception("Was unable to obtain CSRF token from server. Response code: " + str(response_code))
    csrf_token = response['csrfToken']
    logger.info("CSRF token=" + csrf_token)
    return csrf_token


def post(url_postfix, data):
    session = generate_session()
    url = _server_api_address + url_postfix
    logger.info("Performing post to " + url)
    headers = {'X-CSRFToken': get_csrf_token(session), 'Accept': 'application/json', "Referer": url}

    response = session.post(url, json=data, verify=_validate_server_identity, headers=headers, timeout=_call_timeout)
    logger.info("Server response:" + str(response.status_code) + "-" + str(response.json()))
    return response.status_code, response.json()


def get(url_postfix):
    session = generate_session()
    url = _server_api_address + url_postfix
    logger.info("Performing get to " + url)
    headers = {'Accept': 'application/json'}
    response = session.get(url, verify=_validate_server_identity, headers=headers, timeout=_call_timeout)
    logger.info("Server response:" + str(response.status_code) + "-" + str(response.content))
    return response.status_code, response.json()


def add_devices(devices):
    return post('/api/addDevices', {"devices": devices})


def add_ports(ports):
    return post('/api/addPorts', {"ports": ports})


def report_sensor_health(health_info):
    return post('/api/sensorHealth', health_info)
