"""
Background monitoring service for Pushover notifications.
Runs as a daemon thread to monitor network devices and sensors.
"""
import datetime
import logging
import threading
import time
from django.utils import timezone
from easy_net_visibility_server.models import Sensor, Device
from easy_net_visibility_server.pushover_notifier import get_notifier

logger = logging.getLogger(__name__)


class NetworkMonitoringService:
    """
    Background service that monitors network devices and sensors for
    timeout/offline events and sends Pushover notifications.
    """
    
    def __init__(self, check_interval_seconds=300):
        """
        Initialize the monitoring service.
        
        Args:
            check_interval_seconds: How often to check for offline devices/gateways (default: 300 = 5 minutes)
        """
        self.check_interval_seconds = check_interval_seconds
        self.notifier = get_notifier()
        self._thread = None
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the monitoring service in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Network monitoring service is already running")
            return
        
        logger.info(f"Starting network monitoring service (check interval: {self.check_interval_seconds}s)")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the monitoring service."""
        if self._thread is None:
            return
            
        logger.info("Stopping network monitoring service")
        self._stop_event.set()
        self._thread.join(timeout=5)
        
    def _monitoring_loop(self):
        """Main monitoring loop that runs in the background."""
        logger.info("Network monitoring loop started")
        
        while not self._stop_event.is_set():
            try:
                self._check_gateway_timeouts()
                self._check_device_offline()
            except Exception as e:
                logger.exception(f"Error in monitoring loop: {e}")
            
            # Wait for the configured interval or until stop is requested
            self._stop_event.wait(timeout=self.check_interval_seconds)
        
        logger.info("Network monitoring loop stopped")
    
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
            # Check if we've already notified about this sensor being offline
            # Only notify again if it's been offline for at least 24 hours since last notification
            should_notify = (
                sensor.last_notified_timeout is None or
                sensor.last_notified_timeout < timezone.now() - datetime.timedelta(hours=24)
            )
            
            if should_notify:
                minutes_offline = sensor.time_since_last_seen()
                self.notifier.notify_gateway_timeout(sensor.hostname or sensor.mac, minutes_offline)
                sensor.last_notified_timeout = timezone.now()
                sensor.save(update_fields=['last_notified_timeout'])
                logger.info(f"Gateway timeout notification sent: {sensor.hostname} ({sensor.mac}) - {minutes_offline} minutes offline")
        
        # Clear notification timestamps for sensors that are back online
        online_sensors = Sensor.objects.filter(
            last_seen__gte=timeout_threshold,
            last_notified_timeout__isnull=False
        )
        updated_count = online_sensors.update(last_notified_timeout=None)
        if updated_count > 0:
            logger.info(f"Cleared notification state for {updated_count} sensor(s) that came back online")

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
            # Check if we've already notified about this device being offline
            # Only notify again if it's been offline for at least 24 hours since last notification
            should_notify = (
                device.last_notified_offline is None or
                device.last_notified_offline < timezone.now() - datetime.timedelta(hours=24)
            )
            
            if should_notify:
                device_name = device.name() or device.mac
                self.notifier.notify_device_offline(device_name, device.ip, device.mac)
                device.last_notified_offline = timezone.now()
                device.save(update_fields=['last_notified_offline'])
                logger.info(f"Device offline notification sent: {device_name} ({device.ip}) - {device.mac}")
        
        # Clear notification timestamps for devices that are back online
        online_devices = Device.objects.filter(
            last_seen__gte=offline_threshold,
            last_notified_offline__isnull=False
        )
        updated_count = online_devices.update(last_notified_offline=None)
        if updated_count > 0:
            logger.info(f"Cleared notification state for {updated_count} device(s) that came back online")


# Global monitoring service instance
_monitoring_service = None
_service_lock = threading.Lock()


def get_monitoring_service() -> NetworkMonitoringService:
    """Get or create the global NetworkMonitoringService instance."""
    global _monitoring_service
    if _monitoring_service is None:
        with _service_lock:
            if _monitoring_service is None:
                _monitoring_service = NetworkMonitoringService()
    return _monitoring_service
