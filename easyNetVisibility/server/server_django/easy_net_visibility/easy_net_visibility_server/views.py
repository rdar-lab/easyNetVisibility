from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Device, Port, Sensor
from django.contrib.messages import add_message, constants


@login_required
def home(request):
    devices_list = Device.objects.prefetch_related('port_set').order_by('ip')
    visible_devices = [device for device in devices_list if not device.is_hidden()]
    return render(request, 'home.html', {'deviceList': visible_devices})


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
