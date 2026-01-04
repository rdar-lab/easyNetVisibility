from django.contrib import admin

from .models import Device, Port, Sensor

# Register your models here.
admin.site.register(Device)
admin.site.register(Port)
admin.site.register(Sensor)
