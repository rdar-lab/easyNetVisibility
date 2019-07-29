import datetime

import traceback
from flask import request, render_template, redirect, jsonify, flash

import db
# Local Scripts
import email
import general_utils
import validators
from webapp import app


@app.route('/api/csrf')
def get_csrf_token():
    return render_template('csrf.html')


@app.route('/api/addDevice', methods=['POST'])
def add_device():
    new_device_data = general_utils.read_device_details_from_request_body()
    mac = new_device_data['mac']
    if len(mac) == 0:
        return jsonify(status="Error", reason="Must Supply MAC Address")
    if not validators.mac_address(mac):
        return jsonify(status="Error", reason="Invalid MAC Address")
    ip = new_device_data['ip']
    if len(ip) > 0 and not validators.ip_address(ip):
        return jsonify(status="Error", reason="Invalid IP Address")
    hostname = new_device_data['hostname']
    if len(hostname) > 0 and not validators.hostname(hostname):
        return jsonify(status="Error", reason="Invalid Hostname")

    existing_devices = db.find_device_by_mac(mac)

    if len(existing_devices) == 0:
        try:
            db.add_device(new_device_data)

            email_body = render_template('emails/addDevice.html', deviceInfo=new_device_data,
                                         serverUrl=app.config['SERVER_URL'])
            email.email_user("New Device Detected", email_body)
            return jsonify(status="Success", reason="Device added")
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error adding device:' + str(e))
    else:
        # device already exists
        existing_device = existing_devices[0]
        existing_device['hostname'] = hostname
        existing_device['ip'] = ip
        existing_device['last_seen'] = datetime.datetime.now()

        try:
            db.update_device(existing_device)
            return jsonify(status="Success", reason="Device updated")
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error updating device:' + str(e))


@app.route('/api/addPort', methods=['POST'])
def add_port():
    mac = ''
    port_num = ''
    protocol = ''
    name = ''
    product = ''
    version = ''
    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "mac":
                mac = request.form['mac']
                mac = validators.convert_mac(mac)
            if key == "port":
                port_num = request.form['port']
            if key == "protocol":
                protocol = request.form['protocol']
            if key == "name":
                name = request.form['name']
            if key == "version":
                version = request.form['version']
            if key == "product":
                product = request.form['product']
    if len(mac) == 0:
        return jsonify(status='error', reason='missing mac address')
    if len(port_num) == 0:
        return jsonify(status='error', reason='missing port number')
    if len(protocol) == 0:
        return jsonify(status='error', reason='missing protocol')
    if len(name) == 0:
        return jsonify(status='error', reason='missing port name')
    if len(version) == 0:
        version = 'Unknown'
    if len(product) == 0:
        product = 'Unknown'

    port_data = {'port_num': port_num,
                 'protocol': protocol,
                 'name': name,
                 'product': product,
                 'version': version,
                 'first_seen': datetime.datetime.now(),
                 'last_seen': datetime.datetime.now()}

    existing_devices = db.find_device_by_mac(mac)
    if len(existing_devices) == 0:
        return jsonify(status='error', reason='device not found')

    existing_device = existing_devices[0]
    port_data['device_id'] = existing_device['device_id']

    existing_ports = db.find_ports_by_device_and_num(existing_device['device_id'], port_num)

    if len(existing_ports) == 0:
        try:
            db.add_port(port_data)
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error :' + str(e))

    else:
        existing_port = existing_ports[0]
        existing_port['last_seen'] = datetime.datetime.now()
        try:
            db.update_port(existing_port)
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error :' + str(e))

    return jsonify(status='success', reason='port information updated')


@app.route('/api/getConfig', methods=['GET'])
def get_config():
    device_list = general_utils.read_all_devices()
    return jsonify(deviceList=device_list)


@app.route('/api/sensorHealth', methods=['POST'])
def sensor_health():
    sensor_mac = ''
    sensor_hostname = ''

    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "mac":
                sensor_mac = request.form['mac']
            if key == "hostname":
                sensor_hostname = request.form['hostname']

    if len(sensor_mac) == 0:
        print "unknown sensor mac"
        flash(u'Unknown Sensor MAC', 'error')
        return redirect('/')
    if len(sensor_hostname) == 0:
        print "unknown sensor Hostname"
        flash(u'unknown sensor Hostname', 'error')
        return redirect('/status')

    sensor_info = {'mac': sensor_mac,
                   'hostname': sensor_hostname,
                   'first_seen': datetime.datetime.now(),
                   'last_seen': datetime.datetime.now()}

    sensors = db.find_sensor_by_mac(sensor_mac)
    if len(sensors) == 0:
        try:
            db.add_sensor(sensor_info)
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error :' + str(e))
    else:
        try:
            sensor = sensors[0]
            sensor['hostname'] = sensor_info['hostname']
            sensor['last_seen'] = datetime.datetime.now()
            db.update_sensor(sensor)
        except Exception as e:
            traceback.print_exc()
            return jsonify(status="Error", reason='Error :' + str(e))

    return jsonify(status='success', reason='sensor information updated')
