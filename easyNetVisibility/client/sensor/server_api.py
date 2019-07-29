import logging
import requests

server_api_address = None
server_username = None
server_password = None
validate_server_identity = False

logger = logging.getLogger('EasyNetVisibility')


def init(param_server_api_address, param_server_username, param_server_password, param_validate_server_identity):
    global server_api_address
    global server_username
    global server_password
    global validate_server_identity

    server_api_address = param_server_api_address
    if server_username is not None and len(server_username) > 0:
        server_username = param_server_username
        server_password = param_server_password

    validate_server_identity = param_validate_server_identity
    logger.info("Server connection set for server:" + server_api_address)


def generate_session():
    session = requests.Session()
    if server_username is not None:
        session.auth = (server_username, server_password)
    return session


def get_csrf_token(session):
    logger.info("Obtaining CSRF token")
    csrf_url = server_api_address + '/api/csrf'
    auth = session.get(csrf_url, verify=validate_server_identity, timeout=5000)
    csrf_token = auth.content
    logger.info("CSRF token=" + csrf_token)
    return csrf_token


def post(url_postfix, data):
    session = generate_session()
    url = server_api_address + url_postfix
    logger.info("Performing post to " + url)
    data['csrf_token'] = get_csrf_token(session)
    response = session.post(url, data=data, verify=validate_server_identity, headers={"referer": url}, timeout=5000)
    logger.info("Server response:" + str(response.status_code) + "-" + str(response.content))
    return response


def get(url_postfix):
    session = generate_session()
    url = server_api_address + url_postfix
    logger.info("Performing get to " + url)
    response = session.get(url, verify=validate_server_identity, timeout=5000)
    logger.info("Server response:" + str(response.status_code) + "-" + str(response.content))
    return response.content


def add_device(device_hostname, device_ip, device_mac, device_vendor):
    data = {'hostname': device_hostname,
            'ip': device_ip,
            'mac': device_mac,
            'vendor': device_vendor}

    return post('/api/addDevice', data)


def add_port(port_info):
    return post('/api/addPort', port_info)


def get_config():
    return get('/api/getConfig')


def report_sensor_health(health_info):
    return post('/api/sensorHealth', health_info)
