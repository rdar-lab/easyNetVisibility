from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Device, Port, Sensor
from django.contrib.messages import add_message, constants
import ipaddress
from collections import defaultdict


def get_subnet(ip_address, prefix_length=24):
    """
    Calculate the subnet for a given IP address.
    Uses /24 (255.255.255.0) as default subnet mask.
    Returns subnet in CIDR notation (e.g., '192.168.1.0/24').
    Returns 'unknown' for invalid or empty IP addresses.
    """
    try:
        network = ipaddress.ip_network(f"{ip_address}/{prefix_length}", strict=False)
        return str(network)
    except (ValueError, ipaddress.AddressValueError):
        # If IP is invalid or empty, return a default group
        return "unknown"


@login_required
def home(request):
    devices_list = Device.objects.prefetch_related('port_set').order_by('ip')
    visible_devices = [device for device in devices_list if not device.is_hidden()]
    
    # Group devices by subnet
    devices_by_subnet = defaultdict(list)
    for device in visible_devices:
        subnet = get_subnet(device.ip)
        devices_by_subnet[subnet].append(device)
    
    # Convert to sorted list of tuples (subnet, devices) for template
    # Sort by network address for proper ordering
    def sort_key(item):
        subnet_str = item[0]
        if subnet_str == "unknown":
            # Put unknown subnets at the end
            return (1, subnet_str)
        try:
            return (0, ipaddress.ip_network(subnet_str))
        except (ValueError, ipaddress.AddressValueError):
            return (1, subnet_str)
    
    grouped_devices = sorted(devices_by_subnet.items(), key=sort_key)
    
    return render(request, 'home.html', {
        'deviceList': visible_devices,
        'groupedDevices': grouped_devices
    })


@login_required
def rename_device(request):
    try:
        device_id = request.POST['device_id']
        nickname = request.POST['nickname']

        if nickname is None or len(nickname) == 0:
            raise Exception("Nickname must not be empty")

        device = Device.objects.get(pk=device_id)
        if device is None:
            raise Exception("Device " + device_id + " not found in DB")

        device.nickname = nickname
        device.save()
        add_message(request, constants.INFO, "Device updated successfully")
    except Exception as exp:
        add_message(request, constants.WARNING, str(exp))

    return home(request)


@login_required
def delete_device(request):
    try:
        device_id = request.POST['device_id']

        device = Device.objects.get(pk=device_id)
        if device is None:
            raise Exception("Device " + device_id + " not found in DB")

        device.delete()
        add_message(request, constants.INFO, "Device deleted successfully")
    except Exception as exp:
        add_message(request, constants.WARNING, str(exp))

    return home(request)


@login_required
def delete_sensor(request):
    try:
        sensor_id = request.POST['sensor_id']

        sensor = Sensor.objects.get(pk=sensor_id)
        if sensor is None:
            raise Exception("Sensor " + sensor_id + " not found in DB")

        sensor.delete()
        add_message(request, constants.INFO, "Sensor deleted successfully")
    except Exception as exp:
        add_message(request, constants.WARNING, str(exp))

    return home(request)


@login_required
def device_info(request, device_id):
    try:
        device = Device.objects.prefetch_related('port_set').get(pk=device_id)
        if device is None:
            raise Exception("Device " + device_id + " not found in DB")

        return render(request, 'device.html', {'deviceInfo': device})
    except Exception as exp:
        add_message(request, constants.WARNING, str(exp))

    return home(request)


@login_required
def status(request):
    sensors_list = Sensor.objects.order_by('first_seen')
    return render(request, 'status.html', {'sensors_list': sensors_list})
