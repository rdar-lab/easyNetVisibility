import datetime

import traceback
from flask import render_template
from flask import request, redirect, flash

import db
import general_utils
from webapp import app


# Local Scripts


@app.route('/')
def home_page():
    device_list = general_utils.read_all_devices()
    return render_template('index.html', deviceList=device_list)


@app.route('/renameDevice', methods=['POST'])
def rename_device():
    device_id = ''
    nickname = ''

    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "device_id":
                device_id = request.form['device_id']
            if key == "nickname":
                nickname = request.form['nickname']
    if len(device_id) == 0:
        flash(u'Device ID Missing For Device', 'error')
        return redirect('/')
    if len(nickname) == 0:
        flash(u'New Name Must Actually Have Words', 'error')
        return redirect('/')

    existing_devices = db.find_device_by_device_id(device_id)
    if len(existing_devices) == 0:
        flash(u'Error renaming device, unknown device', 'error')
        return redirect('/')
    else:
        existing_device = existing_devices[0]
        existing_device['nickname'] = nickname

        try:
            db.update_device(existing_device)
            flash(u'Device renamed', 'success')
        except Exception as e:
            traceback.print_exc()
            flash(u'error calling server api: ' + str(e), 'error')

        return redirect('/')


@app.route('/deleteDevice', methods=['POST'])
def delete_device():
    device_id = ''
    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "device_id":
                device_id = request.form['device_id']
    if len(device_id) == 0:
        flash(u'Device ID Missing For Device', 'error')
        return redirect('/')

    existing_devices = db.find_device_by_device_id(device_id)
    if len(existing_devices) == 0:
        flash(u'Error renaming device, unknown device', 'error')
        return redirect('/')
    else:
        existing_device = existing_devices[0]
        try:
            db.delete_device(existing_device['device_id'])
            flash(u'Device removed', 'success')
        except Exception as e:
            traceback.print_exc()
            flash(u'Error: ' + str(e), 'error')

        return redirect('/')


@app.route('/device/<device_id>', methods=['GET'])
def get_device_info(device_id):
    existing_devices = db.find_device_by_device_id(device_id)
    if len(existing_devices) == 0:
        flash(u'Error finding device', 'error')
        return redirect('/')
    else:
        host = existing_devices[0]
        device_info = general_utils.translate_device_info(host, True)

        return render_template('device.html', deviceInfo=device_info)


@app.route('/status')
def status():
    sensors = db.find_all_sensors()
    for sensor in sensors:
        last_seen = sensor['last_seen']
        time_since_last_seen = int((datetime.datetime.now() - last_seen).total_seconds() / 60.0)
        sensor['time_since_last_seen'] = time_since_last_seen

    return render_template('status.html', sensorInfo=sensors)


@app.route('/deleteSensor', methods=['POST'])
def delete_sensor():
    sensor_id = ''
    f = request.form
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "sensor_id":
                sensor_id = request.form['sensor_id']
    if len(sensor_id) == 0:
        print "unknown sensor"
        flash(u'Unknown Sensor ID', 'error')
        return redirect('/status')

    sensors = db.find_sensor_by_sensor_id(sensor_id)
    if len(sensors) == 0:
        flash(u'Error renaming sensor, unknown sensor', 'error')
    else:
        sensor = sensors[0]
        try:
            db.delete_sensor(sensor['sensor_id'])
            flash(u'Sensor Deleted', 'success')
        except Exception as e:
            traceback.print_exc()
            flash(u'Error: ' + str(e), 'error')
    return redirect('/status')
