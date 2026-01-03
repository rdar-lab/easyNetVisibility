"""
Django management command to monitor network devices and sensors.
This command checks for gateway timeouts and device offline events,
sending Pushover notifications based on configuration.
"""
import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from easy_net_visibility_server.models import Sensor, Device
from easy_net_visibility_server.pushover_notifier import get_notifier

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor sensors and devices for timeout/offline events and send Pushover notifications'

    def __init__(self):
        super().__init__()
        self.notifier = get_notifier()
        self.notified_sensors = set()  # Track which sensors we've already notified about
        self.notified_devices = set()  # Track which devices we've already notified about

    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('Starting network monitoring...'))
        
        # Check gateway (sensor) timeouts
        self._check_gateway_timeouts()
        
        # Check device offline status
        self._check_device_offline()
        
        self.stdout.write(self.style.SUCCESS('Monitoring check complete'))

    def _check_gateway_timeouts(self):
        """Check if any gateways (sensors) have timed out."""
        if not self.notifier.alert_gateway_timeout:
            logger.debug("Gateway timeout alerts are disabled")
            return
        
        timeout_minutes = self.notifier.gateway_timeout_minutes
        timeout_threshold = timezone.now() - datetime.timedelta(minutes=timeout_minutes)
        
        # Find sensors that are offline
        offline_sensors = Sensor.objects.filter(last_seen__lt=timeout_threshold)
        
        for sensor in offline_sensors:
            sensor_key = sensor.mac
            
            # Only notify once per sensor until it comes back online
            if sensor_key not in self.notified_sensors:
                minutes_offline = sensor.time_since_last_seen()
                self.notifier.notify_gateway_timeout(sensor.hostname or sensor.mac, minutes_offline)
                self.notified_sensors.add(sensor_key)
                self.stdout.write(
                    self.style.WARNING(
                        f"Gateway timeout: {sensor.hostname} ({sensor.mac}) - {minutes_offline} minutes offline"
                    )
                )
        
        # Clear notifications for sensors that are back online
        online_sensors = Sensor.objects.filter(last_seen__gte=timeout_threshold)
        for sensor in online_sensors:
            self.notified_sensors.discard(sensor.mac)

    def _check_device_offline(self):
        """Check if any devices have gone offline."""
        if not self.notifier.alert_device_offline:
            logger.debug("Device offline alerts are disabled")
            return
        
        # A device is considered offline if not seen in the last 6 hours
        # This matches the online() method in the Device model
        offline_threshold = timezone.now() - datetime.timedelta(hours=6)
        
        # Find devices that were previously online but are now offline
        # We only care about devices with nicknames (user has marked them as important)
        offline_devices = Device.objects.filter(
            last_seen__lt=offline_threshold
        ).exclude(nickname__isnull=True).exclude(nickname='')
        
        for device in offline_devices:
            device_key = device.mac
            
            # Only notify once per device until it comes back online
            if device_key not in self.notified_devices:
                device_name = device.name() or device.mac
                self.notifier.notify_device_offline(device_name, device.ip, device.mac)
                self.notified_devices.add(device_key)
                self.stdout.write(
                    self.style.WARNING(
                        f"Device offline: {device_name} ({device.ip}) - {device.mac}"
                    )
                )
        
        # Clear notifications for devices that are back online
        online_devices = Device.objects.filter(last_seen__gte=offline_threshold)
        for device in online_devices:
            self.notified_devices.discard(device.mac)
