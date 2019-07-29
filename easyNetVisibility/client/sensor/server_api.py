import base64
import requests
import urllib2
import logging

server_api_address = None
server_username = None
server_password = None

logger = logging.getLogger('EasyNetVisibility')


def init(param_server_api_address, param_server_username, param_server_password):
    global server_api_address
    global server_username
    global server_password

    server_api_address = param_server_api_address
    if server_username is not None and len(server_username) > 0:
        server_username = param_server_username
        server_password = param_server_password

    logger.info("Server connection set for server:" + server_api_address)


def generate_session():
    session = requests.Session()
    if server_username is not None:
        session.auth = (server_username, server_password)
    return session


def get_csrf_token(session):
    logger.info("Obtaining CSRF token")
    csrf_url = server_api_address + '/api/csrf'
    auth = session.get(csrf_url, verify=True, timeout=5000)
    csrf_token = auth.content
    logger.info("CSRF token=" + csrf_token)
    return csrf_token


def post(url_postfix, data):
    session = generate_session()
    url = server_api_address + url_postfix
    logger.info("Performing post to " + url)
    data['csrf_token'] = get_csrf_token(session)
    response = session.post(url, data=data, verify=True, headers={"referer": url}, timeout=5000)
    logger.info("Server response:" + str(response.status_code) + "-" + str(response.content))
    return response


def get(url_postfix):
    url = server_api_address + url_postfix
    logger.info("Performing get to " + url)
    req = urllib2.Request(url)
    if server_username is not None:
        base64string = base64.b64encode('%s:%s' % (server_password, server_password))
        req.add_header("Authorization", "Basic %s" % base64string)
    response = urllib2.urlopen(req)
    result = response.read()
    logger.info("Server response:" + str(result))
    return result


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
