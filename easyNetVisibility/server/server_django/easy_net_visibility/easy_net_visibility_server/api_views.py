import datetime
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import get_token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import validators
from .models import Device, Port, Sensor


def read_device_details_from_request_body(request):
    hostname = ''
    ip = ''
    mac = ''
    vendor = ''

    f = request.POST
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "hostname":
                hostname = request.POST['hostname']
            if key == "ip":
                ip = request.POST['ip']
            if key == "mac":
                mac = request.POST['mac']
                # Convert mac to uppercase alphanumeric
                mac = validators.convert_mac(mac)
            if key == "vendor":
                vendor = request.POST['vendor']

    device = Device()
    device.hostname = hostname
    device.ip = ip
    device.mac = mac
    device.vendor = vendor
    device.first_seen = datetime.datetime.now()
    device.last_seen = datetime.datetime.now()

    return device


@api_view(['GET', 'POST'])
def get_csrf_token(request):
    return HttpResponse(get_token(request))


@api_view(['POST'])
def add_device(request):
    new_device_data = read_device_details_from_request_body(request)
    mac = new_device_data.mac
    if len(mac) == 0:
        return return_error("Must Supply MAC Address")
    if not validators.mac_address(mac):
        return return_error("Invalid MAC Address")
    ip = new_device_data.ip
    if len(ip) > 0 and not validators.ip_address(ip):
        return return_error("Invalid IP Address")
    hostname = new_device_data.hostname
    if len(hostname) > 0 and not validators.hostname(hostname):
        return return_error("Invalid Hostname")

    existing_devices = Device.objects.filter(mac=mac)

    if len(existing_devices) == 0:
        try:
            new_device_data.save()

            # email_body = render_template('emails/addDevice.html', deviceInfo=new_device_data,
            #                              serverUrl=app.config['SERVER_URL'])
            # email.email_user("New Device Detected", email_body)
            return return_success("Device added")
        except Exception as e:
            traceback.print_exc()
            return return_error('Error adding device:' + str(e))
    else:
        # device already exists
        existing_device = existing_devices[0]
        existing_device.hostname = hostname
        existing_device.ip = ip
        existing_device.last_seen = datetime.datetime.now()

        try:
            existing_device.save()
            return return_success("Device updated")
        except Exception as e:
            traceback.print_exc()
            return return_error('Error updating device:' + str(e))


@api_view(['POST'])
def add_port(request):
    mac = ''
    port_num = ''
    protocol = ''
    name = ''
    product = ''
    version = ''
    f = request.POST
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "mac":
                mac = request.POST['mac']
                mac = validators.convert_mac(mac)
            if key == "port":
                port_num = request.POST['port']
            if key == "protocol":
                protocol = request.POST['protocol']
            if key == "name":
                name = request.POST['name']
            if key == "version":
                version = request.POST['version']
            if key == "product":
                product = request.POST['product']
    if len(mac) == 0:
        return return_error('missing mac address')
    if len(port_num) == 0:
        return return_error('missing port number')
    if len(protocol) == 0:
        return return_error('missing protocol')
    if len(name) == 0:
        return return_error('missing port name')
    if len(version) == 0:
        version = 'Unknown'
    if len(product) == 0:
        product = 'Unknown'

    port_data = Port()
    port_data.port_num = port_num
    port_data.protocol = protocol
    port_data.name = name
    port_data.product = product
    port_data.version = version
    port_data.first_seen = datetime.datetime.now()
    port_data.last_seen = datetime.datetime.now()

    existing_devices = Device.objects.filter(mac=mac)
    if len(existing_devices) == 0:
        return return_error('device not found')

    existing_device = existing_devices[0]
    port_data.device = existing_device

    existing_ports = Port.objects.filter(device=existing_device, port_num=port_num)

    if len(existing_ports) == 0:
        try:
            port_data.save()
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e))

    else:
        existing_port = existing_ports[0]

        # TODO: only last seen is updated, should other information be updated as well?
        existing_port.last_seen = datetime.datetime.now()
        try:
            existing_port.save()
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e))

    return return_success('port information updated')


@api_view(['POST'])
def sensor_health(request):
    sensor_mac = ''
    sensor_hostname = ''

    f = request.POST
    for key in f.keys():
        for _ in f.getlist(key):
            if key == "mac":
                sensor_mac = request.POST['mac']
            if key == "hostname":
                sensor_hostname = request.POST['hostname']

    if len(sensor_mac) == 0:
        print("unknown sensor mac")
        return return_error('Unknown Sensor MAC')

    if len(sensor_hostname) == 0:
        print("unknown sensor Hostname")
        return return_error('unknown sensor Hostname')

    sensor_info = Sensor()
    sensor_info.mac = sensor_mac
    sensor_info.hostname = sensor_hostname
    sensor_info.first_seen = datetime.datetime.now()
    sensor_info.last_seen = datetime.datetime.now()

    sensors = Sensor.objects.filter(mac=sensor_mac)
    if len(sensors) == 0:
        try:
            sensor_info.save()
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e))
    else:
        try:
            sensor = sensors[0]
            sensor.hostname = sensor_info.hostname
            sensor.last_seen = datetime.datetime.now()
            sensor.save()
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e))

    return return_success('sensor information updated')


def return_success(message):
    return Response({"message": message})


def return_error(error):
    return Response({"error": error}, status=500)
