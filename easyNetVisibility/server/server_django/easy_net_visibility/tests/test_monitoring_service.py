"""
Tests for the monitoring service that runs as a background thread.
"""
import datetime
import time
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from easy_net_visibility_server.models import Device, Sensor
from easy_net_visibility_server.monitoring_service import NetworkMonitoringService


class TestNetworkMonitoringService(TestCase):
    """Test the NetworkMonitoringService background service"""

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_starts_and_stops(self, mock_get_notifier):
        """Test that the monitoring service can start and stop cleanly"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = False
        mock_notifier.alert_device_offline = False
        mock_get_notifier.return_value = mock_notifier

        # Create service with very short interval for testing
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Start the service
        service.start()
        self.assertIsNotNone(service._thread)
        self.assertTrue(service._thread.is_alive())

        # Wait a bit to ensure thread is running
        time.sleep(0.2)

        # Stop the service
        service.stop()
        self.assertFalse(service._thread.is_alive())

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_checks_gateway_timeout(self, mock_get_notifier):
        """Test that the service checks for gateway timeouts"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_notifier.alert_device_offline = False
        mock_get_notifier.return_value = mock_notifier

        # Create an offline sensor
        offline_sensor = Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=20)
        )

        # Create service with very short interval
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Run one check manually
        service._check_gateway_timeouts()

        # Verify notification was sent
        mock_notifier.notify_gateway_timeout.assert_called_once()

        # Verify the sensor was marked as notified
        offline_sensor.refresh_from_db()
        self.assertIsNotNone(offline_sensor.last_notified_timeout)

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_checks_device_offline(self, mock_get_notifier):
        """Test that the service checks for offline devices"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = False
        mock_notifier.alert_device_offline = True
        mock_get_notifier.return_value = mock_notifier

        # Create an offline device with nickname
        offline_device = Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            nickname='My Device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=7)
        )

        # Create service
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Run one check manually
        service._check_device_offline()

        # Verify notification was sent
        mock_notifier.notify_device_offline.assert_called_once()

        # Verify the device was marked as notified
        offline_device.refresh_from_db()
        self.assertIsNotNone(offline_device.last_notified_offline)

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_handles_errors_gracefully(self, mock_get_notifier):
        """Test that the service continues running even if one check fails"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_notifier.alert_device_offline = True
        # Make notify_gateway_timeout raise an exception
        mock_notifier.notify_gateway_timeout.side_effect = Exception("Test error")
        mock_get_notifier.return_value = mock_notifier

        # Create service
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Create an offline sensor to trigger the error
        Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=20)
        )

        # Start the service - it should not crash
        service.start()
        time.sleep(0.3)  # Let it run a few cycles

        # Service should still be running despite the error
        self.assertTrue(service._thread.is_alive())

        # Stop the service
        service.stop()

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_double_start_warning(self, mock_get_notifier):
        """Test that starting an already running service logs a warning"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = False
        mock_notifier.alert_device_offline = False
        mock_get_notifier.return_value = mock_notifier

        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Start the service
        service.start()
        first_thread = service._thread

        # Try to start again
        with self.assertLogs('easy_net_visibility_server.monitoring_service', level='WARNING') as cm:
            service.start()
            self.assertIn('already running', cm.output[0])

        # Should be the same thread
        self.assertIs(service._thread, first_thread)

        # Stop the service
        service.stop()

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_clears_online_sensors(self, mock_get_notifier):
        """Test that notification state is cleared when sensors come back online"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_notifier.alert_device_offline = False
        mock_get_notifier.return_value = mock_notifier

        # Create an online sensor that was previously notified
        online_sensor = Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=2),
            last_notified_timeout=timezone.now() - datetime.timedelta(hours=1)
        )

        # Create service
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Run one check
        service._check_gateway_timeouts()

        # Verify notification state was cleared
        online_sensor.refresh_from_db()
        self.assertIsNone(online_sensor.last_notified_timeout)

    @patch('easy_net_visibility_server.monitoring_service.get_notifier')
    def test_service_clears_online_devices(self, mock_get_notifier):
        """Test that notification state is cleared when devices come back online"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = False
        mock_notifier.alert_device_offline = True
        mock_get_notifier.return_value = mock_notifier

        # Create an online device that was previously notified
        online_device = Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            nickname='My Device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=1),
            last_notified_offline=timezone.now() - datetime.timedelta(hours=10)
        )

        # Create service
        service = NetworkMonitoringService(check_interval_seconds=0.1)

        # Run one check
        service._check_device_offline()

        # Verify notification state was cleared
        online_device.refresh_from_db()
        self.assertIsNone(online_device.last_notified_offline)
