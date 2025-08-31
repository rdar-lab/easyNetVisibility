import datetime
import traceback

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import get_token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import validators
from .models import Device, Port, Sensor

# If a device was seen within this threshold, don't update last_seen again
# This is disabled because it didn't effect the performance in a meaningful way
_LAST_SEEN_THRESHOLD_MINUTES = 0

def client_expects_json(request):
    # Accepts JSON if header or ?format=json
    accept = request.META.get('HTTP_ACCEPT', '')
    if 'application/json' in accept:
        return True
    if request.GET.get('format', '').lower() == 'json':
        return True
    return False

def read_device_details_from_request_body(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    hostname = data.get('hostname', '')
    ip = data.get('ip', '')
    mac = data.get('mac', '')
    vendor = data.get('vendor', '')
    if mac:
        mac = validators.convert_mac(mac)
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
    if not getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
        if client_expects_json(request):
            return JsonResponse({"message": "NOT_REQUIRED"})
        return HttpResponse("NOT_REQUIRED")

    token = get_token(request)
    if client_expects_json(request):
        return JsonResponse({"csrfToken": token})
    return HttpResponse(token)


@api_view(['POST'])
def add_device(request):
    new_device_data = read_device_details_from_request_body(request)
    mac = new_device_data.mac
    if len(mac) == 0:
        return return_error("Must Supply MAC Address", status=400, request=request)
    if not validators.mac_address(mac):
        return return_error("Invalid MAC Address", status=400, request=request)
    ip = new_device_data.ip
    if len(ip) > 0 and not validators.ip_address(ip):
        return return_error("Invalid IP Address", status=400, request=request)
    hostname = new_device_data.hostname
    if len(hostname) > 0 and not validators.hostname(hostname):
        return return_error("Invalid Hostname", status=400, request=request)

    existing_devices = Device.objects.filter(mac=mac)

    if len(existing_devices) == 0:
        try:
            new_device_data.save()
            return return_success("Device added", request=request)
        except Exception as e:
            traceback.print_exc()
            return return_error('Error adding device:' + str(e), request=request)
    else:
        # device already exists
        existing_device = existing_devices[0]
        now = datetime.datetime.now()

        if (existing_device.hostname == hostname and
                existing_device.ip == ip and
                existing_device.last_seen is not None and
                existing_device.last_seen > now - datetime.timedelta(minutes=_LAST_SEEN_THRESHOLD_MINUTES)):
            return return_success("No update needed", request=request)
        else:
            try:
                existing_device.hostname = hostname
                existing_device.ip = ip
                existing_device.last_seen = datetime.datetime.now()
                existing_device.save()
                return return_success("Device updated", request=request)
            except Exception as e:
                traceback.print_exc()
                return return_error('Error updating device:' + str(e), request=request)


@api_view(['POST'])
def add_port(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    mac = data.get('mac', '')
    port_num = data.get('port', '')
    protocol = data.get('protocol', '')
    name = data.get('name', '')
    version = data.get('version', '')
    product = data.get('product', '')

    if mac:
        mac = validators.convert_mac(mac)
    if len(mac) == 0:
        return return_error('missing mac address', status=400, request=request)
    if len(port_num) == 0:
        return return_error('missing port number', status=400, request=request)
    if len(protocol) == 0:
        return return_error('missing protocol', status=400, request=request)
    if len(name) == 0:
        return return_error('missing port name', status=400, request=request)

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
        return return_error('device not found', status=400, request=request)

    existing_device = existing_devices[0]
    port_data.device = existing_device

    existing_ports = Port.objects.filter(device=existing_device, port_num=port_num)

    if len(existing_ports) == 0:
        try:
            port_data.save()
            return return_success('port added', request=request)
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e), request=request)
    else:
        existing_port = existing_ports[0]
        # TODO: only last seen is updated, should other information be updated as well?
        now = datetime.datetime.now()

        if (existing_port.last_seen is not None and
                existing_port.last_seen > now - datetime.timedelta(minutes=_LAST_SEEN_THRESHOLD_MINUTES)):
            return return_success('no update needed', request=request)
        else:
            try:
                existing_port.last_seen = datetime.datetime.now()
                existing_port.save()
                return return_success('port information updated', request=request)
            except Exception as e:
                traceback.print_exc()
                return return_error('Error :' + str(e), request=request)


@api_view(['POST'])
def sensor_health(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    sensor_mac = data.get('mac', '')
    sensor_hostname = data.get('hostname', '')

    if len(sensor_mac) == 0:
        return return_error('Unknown Sensor MAC', status=400, request=request)
    if len(sensor_hostname) == 0:
        return return_error('unknown sensor Hostname', status=400, request=request)

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
            return return_error('Error :' + str(e), request=request)
    else:
        try:
            sensor = sensors[0]
            sensor.hostname = sensor_info.hostname
            sensor.last_seen = datetime.datetime.now()
            sensor.save()
        except Exception as e:
            traceback.print_exc()
            return return_error('Error :' + str(e), request=request)

    return return_success('sensor information updated', request=request)


def return_success(message, request=None):
    if request is not None and client_expects_json(request):
        return JsonResponse({"message": message})
    return Response({"message": message})


def return_error(message, status=500, request=None):
    if request is not None and client_expects_json(request):
        return JsonResponse({'error': message}, status=status)
    return Response({'error': message}, status=status)
