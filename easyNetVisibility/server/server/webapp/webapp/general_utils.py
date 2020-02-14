import datetime

from flask import request

import db
import validators


def split_ip(ip):
    """Split a IP address given as string into a 4-tuple of integers."""
    return tuple(int(part) for part in ip.split('.'))


def read_all_devices():
    device_list = []
    all_devices = db.find_all_devices()
    if all_devices is not None:
        for host in all_devices:
            device_info = translate_device_info(host, False)
            device_list.append(device_info)
    device_list.sort(key=lambda device: split_ip(device['ip'])[3], reverse=False)
    return device_list


def translate_device_info(host, get_ports):
    device_id = host['device_id']
    now = datetime.datetime.now()
    first_seen = host['first_seen']
    first_seen_today = first_seen.date() == now.date()
    last_seen = host['last_seen']
    online = last_seen + datetime.timedelta(minutes=60) > now
    port_list = []
    open_ports = host['open_ports']


    if get_ports == True
        ports = db.find_ports_of_device(device_id)
        open_ports = len(ports)

        for port in ports:
            port_info_tmp = {'first_seen': port['first_seen'].strftime('%Y-%m-%d %H:%M:%S'),
                            'last_seen': port['last_seen'].strftime('%Y-%m-%d %H:%M:%S'),
                            'protocol': port['protocol'],
                            'name': port['name'],
                            'product': port['product'],
                            'version': port['version'],
                            'port': int(port['port_num'])}
            port_list.append(port_info_tmp)
            port_list = sorted(port_list, key=lambda k: k['port'])

    device_info = {'hostname': host['hostname'],
                   'nickname': host['nickname'],
                   'ip': host['ip'],
                   'mac': host['mac'],
                   'vendor': host['vendor'],
                   'first_seen': first_seen.strftime('%Y-%m-%d %H:%M:%S'),
                   'first_seen_today': first_seen_today,
                   'last_seen': last_seen.strftime('%Y-%m-%d %H:%M:%S'),
                   'online': online,
                   'device_id': host['device_id'],
                   'open_ports': open_ports,
                   'port_list': port_list
                   }

    return device_info


def read_device_details_from_request_body():
    hostname = ''
    ip = ''
    mac = ''
    vendor = ''

    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "hostname":
                hostname = request.form['hostname']
            if key == "ip":
                ip = request.form['ip']
            if key == "mac":
                mac = request.form['mac']
                # Convert mac to uppercase alphanumeric
                mac = validators.convert_mac(mac)
            if key == "vendor":
                vendor = request.form['vendor']

    new_device_data = {'hostname': hostname,
                       'nickname': hostname,
                       'ip': ip,
                       'mac': mac,
                       'vendor': vendor,
                       'first_seen': datetime.datetime.now(),
                       'last_seen': datetime.datetime.now()}
    return new_device_data
