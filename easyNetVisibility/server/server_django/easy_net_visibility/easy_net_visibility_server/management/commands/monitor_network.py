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
            # Use select_for_update to prevent race conditions
            try:
                # Re-fetch with lock to ensure atomic check-and-update
                locked_sensor = Sensor.objects.select_for_update(nowait=True).get(pk=sensor.pk)
                
                # Check if we've already notified about this sensor being offline
                # Only notify again if it's been offline for at least 24 hours since last notification
                should_notify = (
                    locked_sensor.last_notified_timeout is None or
                    locked_sensor.last_notified_timeout < timezone.now() - datetime.timedelta(hours=24)
                )
                
                if should_notify:
                    minutes_offline = locked_sensor.time_since_last_seen()
                    self.notifier.notify_gateway_timeout(locked_sensor.hostname or locked_sensor.mac, minutes_offline)
                    locked_sensor.last_notified_timeout = timezone.now()
                    locked_sensor.save(update_fields=['last_notified_timeout'])
                    self.stdout.write(
                        self.style.WARNING(
                            f"Gateway timeout: {locked_sensor.hostname} ({locked_sensor.mac}) - {minutes_offline} minutes offline"
                        )
                    )
            except Exception as e:
                # Skip if we can't acquire lock (another process is handling it)
                logger.debug(f"Skipping sensor {sensor.mac} - could not acquire lock or error occurred: {e}")
                continue
        
        # Clear notification timestamps for sensors that are back online
        online_sensors = Sensor.objects.filter(
            last_seen__gte=timeout_threshold,
            last_notified_timeout__isnull=False
        )
        online_sensors.update(last_notified_timeout=None)

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
            # Use select_for_update to prevent race conditions
            try:
                # Re-fetch with lock to ensure atomic check-and-update
                locked_device = Device.objects.select_for_update(nowait=True).get(pk=device.pk)
                
                # Check if we've already notified about this device being offline
                # Only notify again if it's been offline for at least 24 hours since last notification
                should_notify = (
                    locked_device.last_notified_offline is None or
                    locked_device.last_notified_offline < timezone.now() - datetime.timedelta(hours=24)
                )
                
                if should_notify:
                    device_name = locked_device.name() or locked_device.mac
                    self.notifier.notify_device_offline(device_name, locked_device.ip, locked_device.mac)
                    locked_device.last_notified_offline = timezone.now()
                    locked_device.save(update_fields=['last_notified_offline'])
                    self.stdout.write(
                        self.style.WARNING(
                            f"Device offline: {device_name} ({locked_device.ip}) - {locked_device.mac}"
                        )
                    )
            except Exception as e:
                # Skip if we can't acquire lock (another process is handling it)
                logger.debug(f"Skipping device {device.mac} - could not acquire lock or error occurred: {e}")
                continue
        
        # Clear notification timestamps for devices that are back online
        online_devices = Device.objects.filter(
            last_seen__gte=offline_threshold,
            last_notified_offline__isnull=False
        )
        online_devices.update(last_notified_offline=None)

