"""
Tests for the monitor_network management command.
"""
from io import StringIO
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.utils import timezone
import datetime

from easy_net_visibility_server.models import Device, Sensor


# Test configuration with Pushover enabled
PUSHOVER_TEST_CONFIG = {
    'enabled': True,
    'user_key': 'test_user_key',
    'api_token': 'test_api_token',
    'alert_new_device': False,
    'alert_gateway_timeout': True,
    'alert_device_offline': True,
    'gateway_timeout_minutes': 10
}


class TestMonitorNetworkCommand(TestCase):
    """Test the monitor_network management command"""

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_gateway_timeout_notification(self, mock_get_notifier):
        """Test that offline gateways trigger notifications"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline sensor (last seen 20 minutes ago)
        offline_sensor = Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=20)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was sent
        mock_notifier.notify_gateway_timeout.assert_called_once()
        call_args = mock_notifier.notify_gateway_timeout.call_args
        self.assertIn('test-gateway', call_args[0][0])
        
        # Verify the sensor was marked as notified
        offline_sensor.refresh_from_db()
        self.assertIsNotNone(offline_sensor.last_notified_timeout)

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_gateway_timeout_no_duplicate_notification(self, mock_get_notifier):
        """Test that duplicate notifications are not sent for the same gateway"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline sensor that was recently notified
        Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=20),
            last_notified_timeout=timezone.now() - datetime.timedelta(hours=1)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was NOT sent (already notified recently)
        mock_notifier.notify_gateway_timeout.assert_not_called()

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_gateway_back_online_clears_notification(self, mock_get_notifier):
        """Test that notification state is cleared when gateway comes back online"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = True
        mock_notifier.gateway_timeout_minutes = 10
        mock_get_notifier.return_value = mock_notifier
        
        # Create an online sensor that was previously notified
        online_sensor = Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=2),
            last_notified_timeout=timezone.now() - datetime.timedelta(hours=1)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification state was cleared
        online_sensor.refresh_from_db()
        self.assertIsNone(online_sensor.last_notified_timeout)

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_device_offline_notification(self, mock_get_notifier):
        """Test that offline devices with nicknames trigger notifications"""
        mock_notifier = MagicMock()
        mock_notifier.alert_device_offline = True
        mock_notifier.alert_gateway_timeout = False
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline device with a nickname (last seen 7 hours ago)
        offline_device = Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            nickname='My Device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=7)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was sent
        mock_notifier.notify_device_offline.assert_called_once()
        call_args = mock_notifier.notify_device_offline.call_args
        self.assertIn('My Device', call_args[0][0])
        self.assertEqual(call_args[0][1], '192.168.1.100')
        
        # Verify the device was marked as notified
        offline_device.refresh_from_db()
        self.assertIsNotNone(offline_device.last_notified_offline)

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_device_offline_no_notification_without_nickname(self, mock_get_notifier):
        """Test that offline devices without nicknames do NOT trigger notifications"""
        mock_notifier = MagicMock()
        mock_notifier.alert_device_offline = True
        mock_notifier.alert_gateway_timeout = False
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline device WITHOUT a nickname (last seen 7 hours ago)
        Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=7)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was NOT sent
        mock_notifier.notify_device_offline.assert_not_called()

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_device_offline_no_duplicate_notification(self, mock_get_notifier):
        """Test that duplicate notifications are not sent for the same device"""
        mock_notifier = MagicMock()
        mock_notifier.alert_device_offline = True
        mock_notifier.alert_gateway_timeout = False
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline device that was recently notified
        Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            nickname='My Device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=7),
            last_notified_offline=timezone.now() - datetime.timedelta(hours=1)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was NOT sent (already notified recently)
        mock_notifier.notify_device_offline.assert_not_called()

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_device_back_online_clears_notification(self, mock_get_notifier):
        """Test that notification state is cleared when device comes back online"""
        mock_notifier = MagicMock()
        mock_notifier.alert_device_offline = True
        mock_notifier.alert_gateway_timeout = False
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
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification state was cleared
        online_device.refresh_from_db()
        self.assertIsNone(online_device.last_notified_offline)

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_gateway_monitoring_disabled(self, mock_get_notifier):
        """Test that gateway monitoring respects configuration"""
        mock_notifier = MagicMock()
        mock_notifier.alert_gateway_timeout = False
        mock_notifier.alert_device_offline = False
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline sensor
        Sensor.objects.create(
            mac='AABBCCDDEEFF',
            hostname='test-gateway',
            first_seen=timezone.now() - datetime.timedelta(hours=1),
            last_seen=timezone.now() - datetime.timedelta(minutes=20)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was NOT sent (monitoring disabled)
        mock_notifier.notify_gateway_timeout.assert_not_called()

    @patch('easy_net_visibility_server.management.commands.monitor_network.get_notifier')
    def test_device_monitoring_disabled(self, mock_get_notifier):
        """Test that device monitoring respects configuration"""
        mock_notifier = MagicMock()
        mock_notifier.alert_device_offline = False
        mock_notifier.alert_gateway_timeout = False
        mock_get_notifier.return_value = mock_notifier
        
        # Create an offline device with nickname
        Device.objects.create(
            mac='112233445566',
            hostname='test-device',
            nickname='My Device',
            ip='192.168.1.100',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(hours=7)
        )
        
        # Run the command
        out = StringIO()
        call_command('monitor_network', stdout=out)
        
        # Verify notification was NOT sent (monitoring disabled)
        mock_notifier.notify_device_offline.assert_not_called()
