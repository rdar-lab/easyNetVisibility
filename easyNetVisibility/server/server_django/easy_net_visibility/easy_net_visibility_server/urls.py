from django.urls import path

from . import views, api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('status', views.status, name='status'),
    path('rename_device', views.rename_device, name='rename_device'),
    path('delete_device', views.delete_device, name='delete_device'),
    path('delete_sensor', views.delete_sensor, name='delete_sensor'),
    path('device/<int:device_id>/', views.device_info, name='device_info'),

    path('api/csrf', api_views.get_csrf_token, name="get_csrf_token"),
    path('api/addDevice', api_views.add_device, name="add_device"),
    path('api/addPort', api_views.add_port, name="add_port"),
    path('api/sensorHealth', api_views.sensor_health, name="sensor_health")
]
