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

def _client_expects_json(request):
    # Accepts JSON if header or ?format=json
    accept = request.META.get('HTTP_ACCEPT', '')
    if 'application/json' in accept:
        return True
    if request.GET.get('format', '').lower() == 'json':
        return True
    return False

def _read_device_details_from_request_body(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    return _create_device_obj_from_data(data)


def _create_device_obj_from_data(data) -> Device:
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
        if _client_expects_json(request):
            return JsonResponse({"csrfToken": "NOT_REQUIRED"})
        return HttpResponse("NOT_REQUIRED")

    token = get_token(request)
    if _client_expects_json(request):
        return JsonResponse({"csrfToken": token})
    return HttpResponse(token)


def _process_device(device: Device, existing_devices_map):
    """
    Helper to add or update a device. Returns (status_code: int, error: str or None)
    existing_devices_map: dict mapping mac -> Device
    """
    if len(device.mac) == 0:
        return 400, "Must Supply MAC Address"
    if not validators.mac_address(device.mac):
        return 400, "Invalid MAC Address"
    if len(device.ip) > 0 and not validators.ip_address(device.ip):
        return 400, "Invalid IP Address"
    if len(device.hostname) > 0 and not validators.hostname(device.hostname):
        return 400, "Invalid Hostname"
    now = datetime.datetime.now()
    if device.mac not in existing_devices_map:
        try:
            device.save()
            return 200, None
        except Exception as e:
            traceback.print_exc()
            return 500, f"Error adding device: {str(e)}"
    else:
        existing_device = existing_devices_map.get(device.mac)

        if (existing_device.hostname == device.hostname and
                existing_device.ip == device.ip and
                existing_device.last_seen is not None and
                existing_device.last_seen > now - datetime.timedelta(minutes=_LAST_SEEN_THRESHOLD_MINUTES)):
            return 200, None
        else:
            try:
                existing_device.hostname = device.hostname
                existing_device.ip = device.ip

                # Only update vendor if provided, to avoid overwriting with empty value
                if device.vendor:
                    existing_device.vendor = device.vendor

                existing_device.last_seen = now
                existing_device.save()
                return 200, None
            except Exception as e:
                traceback.print_exc()
                return 500, f"Error updating device: {str(e)}"


@api_view(['POST'])
def add_devices(request):
    # Only accept JSON
    if not _client_expects_json(request):
        return _return_error("Only JSON format supported for batch add.", status=400, request=request)
    try:
        raw_devices = request.data.get('devices', None)
    except Exception:
        return _return_error("Invalid JSON body.", status=400, request=request)
    if not isinstance(raw_devices, list):
        return _return_error("'devices' must be a list.", status=400, request=request)

    devices = [_create_device_obj_from_data(device_data) for device_data in raw_devices]
    existing_devices = Device.objects.filter(mac__in=[d.mac for d in devices if d.mac])
    existing_devices_map = {d.mac: d for d in existing_devices}

    success_count = 0
    errors = []
    for idx, device_obj in enumerate(devices):
        response_code, err = _process_device(device_obj, existing_devices_map)
        if response_code == 200:
            success_count += 1
        else:
            errors.append({"index": idx, "error": err})
    return JsonResponse({
        "success_count": success_count,
        "errors": errors
    }, status=200)


@api_view(['POST'])
def add_device(request):
    device_obj = _read_device_details_from_request_body(request)
    # Fetch existing device for this MAC
    existing_devices = Device.objects.filter(mac=device_obj.mac) if device_obj.mac else None
    existing_devices_map = {d.mac: d for d in existing_devices} if existing_devices else {}
    status_code, err = _process_device(device_obj, existing_devices_map)
    if status_code == 200:
        return _return_success("Device information processed", request=request)
    else:
        return _return_error(err, status=status_code, request=request)



@api_view(['POST'])
def add_port(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    mac = data.get('mac', '')
    port_num = data.get('port', '')

    if mac:
        mac = validators.convert_mac(mac)

    devices = Device.objects.filter(mac=mac) if mac else None
    existing_devices_map = {d.mac: d for d in devices} if devices else {}
    ports = Port.objects.filter(device__mac=mac, port_num=port_num) if port_num and mac else None
    existing_ports_map = {(p.device.mac, str(p.port_num)): p for p in ports} if ports else {}

    code, err = _process_port(data, existing_devices_map, existing_ports_map)
    if code == 200:
        return _return_success('Port information processed', request=request)
    else:
        return _return_error(err, status=code, request=request)


def _process_port(port_data, existing_devices_map, existing_ports_map):
    """
    Helper to add or update a port. Returns (status_code: int, error: str or None)
    existing_devices_map: dict mapping mac -> Device
    existing_ports_map: dict mapping (mac, port_num) -> Port
    """
    mac = port_data.get('mac', '')
    port_num = port_data.get('port', '')
    protocol = port_data.get('protocol', '')
    name = port_data.get('name', '')
    version = port_data.get('version', '') or 'Unknown'
    product = port_data.get('product', '') or 'Unknown'

    if mac:
        mac = validators.convert_mac(mac)
    if len(mac) == 0:
        return 400, 'missing mac address'
    if len(port_num) == 0:
        return 400, 'missing port number'
    if len(protocol) == 0:
        return 400, 'missing protocol'
    if len(name) == 0:
        return 400, 'missing port name'

    device = existing_devices_map.get(mac)
    if not device:
        return 400, 'device not found'

    key = (mac, str(port_num))
    now = datetime.datetime.now()
    if key not in existing_ports_map:
        try:
            port_obj = Port()
            port_obj.device = device
            port_obj.port_num = port_num
            port_obj.protocol = protocol
            port_obj.name = name
            port_obj.product = product
            port_obj.version = version
            port_obj.first_seen = now
            port_obj.last_seen = now
            port_obj.save()
            return 200, None
        except Exception as e:
            traceback.print_exc()
            return 500, f'Error adding port: {str(e)}'
    else:
        port_obj = existing_ports_map[key]
        # Only last_seen is updated, but optionally update other info if provided
        if (port_obj.last_seen is not None and
                port_obj.last_seen > now - datetime.timedelta(minutes=_LAST_SEEN_THRESHOLD_MINUTES)):
            return 200, None
        else:
            try:
                port_obj.last_seen = now
                # Optionally update other fields if provided
                if protocol:
                    port_obj.protocol = protocol
                if name:
                    port_obj.name = name
                if product:
                    port_obj.product = product
                if version:
                    port_obj.version = version
                port_obj.save()
                return 200, None
            except Exception as e:
                traceback.print_exc()
                return 500, f'Error updating port: {str(e)}'


@api_view(['POST'])
def add_ports(request):
    # Only accept JSON
    if not _client_expects_json(request):
        return _return_error("Only JSON format supported for batch add.", status=400, request=request)
    try:
        raw_ports = request.data.get('ports', None)
    except Exception:
        return _return_error("Invalid JSON body.", status=400, request=request)
    if not isinstance(raw_ports, list):
        return _return_error("'ports' must be a list.", status=400, request=request)

    macs = [validators.convert_mac(p.get('mac', '')) for p in raw_ports if p.get('mac', '')]
    port_keys = [str(p.get('port', '')) for p in raw_ports if p.get('port', '')]

    # Bulk fetch all relevant devices and ports
    devices = Device.objects.filter(mac__in=macs)
    existing_devices_map = {d.mac: d for d in devices}
    ports = Port.objects.filter(device__mac__in=macs, port_num__in=[pk for pk in port_keys])
    existing_ports_map = {(p.device.mac, str(p.port_num)): p for p in ports}

    success_count = 0
    errors = []
    for idx, port_data in enumerate(raw_ports):
        code, err = _process_port(port_data, existing_devices_map, existing_ports_map)
        if code == 200:
            success_count += 1
        else:
            errors.append({"index": idx, "error": err})
    return JsonResponse({
        "success_count": success_count,
        "errors": errors
    }, status=200)


@api_view(['POST'])
def sensor_health(request):
    # Use request.data for DRF, fallback to request.POST
    data = getattr(request, 'data', request.POST)
    sensor_mac = data.get('mac', '')
    sensor_hostname = data.get('hostname', '')

    if len(sensor_mac) == 0:
        return _return_error('Unknown Sensor MAC', status=400, request=request)
    if len(sensor_hostname) == 0:
        return _return_error('unknown sensor Hostname', status=400, request=request)

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
            return _return_error('Error :' + str(e), request=request)
    else:
        try:
            sensor = sensors[0]
            sensor.hostname = sensor_info.hostname
            sensor.last_seen = datetime.datetime.now()
            sensor.save()
        except Exception as e:
            traceback.print_exc()
            return _return_error('Error :' + str(e), request=request)

    return _return_success('sensor information updated', request=request)


def _return_success(message, request=None):
    if request is not None and _client_expects_json(request):
        return JsonResponse({"message": message})
    return Response({"message": message})


def _return_error(message, status=500, request=None):
    if request is not None and _client_expects_json(request):
        return JsonResponse({'error': message}, status=status)
    return Response({'error': message}, status=status)
