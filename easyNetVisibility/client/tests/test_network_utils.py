import unittest
from unittest.mock import patch, mock_open
import sys
import os

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import network_utils


class TestNetworkUtilsInit(unittest.TestCase):
    def setUp(self):
        # Reset global variables before each test
        network_utils._interface = None
        network_utils._detected_mac = None
        network_utils._detected_hostname = None

    def test_init_sets_interface(self):
        network_utils.init('eth0')
        self.assertEqual(network_utils.get_interface(), 'eth0')

    def test_get_interface_returns_set_interface(self):
        network_utils.init('wlan0')
        self.assertEqual(network_utils.get_interface(), 'wlan0')

    def test_get_interface_returns_none_when_not_set(self):
        self.assertIsNone(network_utils.get_interface())


class TestConvertMac(unittest.TestCase):
    def test_convert_mac_colon_format(self):
        result = network_utils.convert_mac('aa:bb:cc:dd:ee:ff')
        self.assertEqual(result, 'AABBCCDDEEFF')

    def test_convert_mac_dash_format(self):
        result = network_utils.convert_mac('aa-bb-cc-dd-ee-ff')
        self.assertEqual(result, 'AABBCCDDEEFF')

    def test_convert_mac_already_uppercase(self):
        result = network_utils.convert_mac('AA:BB:CC:DD:EE:FF')
        self.assertEqual(result, 'AABBCCDDEEFF')

    def test_convert_mac_no_separators(self):
        result = network_utils.convert_mac('aabbccddeeff')
        self.assertEqual(result, 'AABBCCDDEEFF')

    def test_convert_mac_mixed_case(self):
        result = network_utils.convert_mac('aA:bB:cC:dD:eE:fF')
        self.assertEqual(result, 'AABBCCDDEEFF')


class TestGetSystemDfgw(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data="""Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT
eth0\t00000000\t0101A8C0\t0003\t0\t0\t0\t00000000\t0\t0\t0
eth0\t0001A8C0\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\t0\t0""")
    def test_get_system_dfgw(self, mock_file):
        result = network_utils.get_system_dfgw()
        self.assertEqual(result, '192.168.1.1')

    @patch('builtins.open', new_callable=mock_open, read_data="""Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT
eth0\t0001A8C0\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\t0\t0""")
    def test_get_system_dfgw_no_gateway(self, mock_file):
        result = network_utils.get_system_dfgw()
        self.assertIsNone(result)


class TestGetIp(unittest.TestCase):
    def setUp(self):
        network_utils._interface = None

    @patch('socket.socket')
    @patch('fcntl.ioctl')
    def test_get_ip_returns_correct_address_when_interface_set(self, mock_ioctl, mock_socket):
        """Test get_ip uses ioctl to fetch IP address when interface is set"""
        network_utils.init('eth0')
        mock_ioctl.return_value = b'\x00' * 20 + b'\xc0\xa8\x01\x64'  # 192.168.1.100
        result = network_utils.get_ip()
        self.assertEqual(result, '192.168.1.100')
        mock_ioctl.assert_called_once()

    def test_get_ip_without_interface(self):
        result = network_utils.get_ip()
        self.assertIsNone(result)


class TestGetNetmask(unittest.TestCase):
    def setUp(self):
        network_utils._interface = None

    @patch('socket.socket')
    @patch('fcntl.ioctl')
    def test_get_netmask(self, mock_ioctl, mock_socket):
        network_utils.init('eth0')
        # 255.255.255.0 = /24
        mock_ioctl.return_value = b'\x00' * 20 + b'\xff\xff\xff\x00'
        result = network_utils.get_netmask()
        self.assertEqual(result, 24)

    @patch('socket.socket')
    @patch('fcntl.ioctl')
    def test_get_netmask_slash_16(self, mock_ioctl, mock_socket):
        network_utils.init('eth0')
        # 255.255.0.0 = /16
        mock_ioctl.return_value = b'\x00' * 20 + b'\xff\xff\x00\x00'
        result = network_utils.get_netmask()
        self.assertEqual(result, 16)

    def test_get_netmask_without_interface(self):
        result = network_utils.get_netmask()
        self.assertIsNone(result)


class TestGetMac(unittest.TestCase):
    def setUp(self):
        network_utils._interface = None
        network_utils._detected_mac = None

    @patch('network_utils.get_if_hwaddr')
    def test_get_mac_success(self, mock_get_if_hwaddr):
        network_utils.init('eth0')
        mock_get_if_hwaddr.return_value = 'aa:bb:cc:dd:ee:ff'
        result = network_utils.get_mac()
        self.assertEqual(result, 'aa:bb:cc:dd:ee:ff')
        mock_get_if_hwaddr.assert_called_once_with('eth0')

    @patch('network_utils.get_if_hwaddr')
    def test_get_mac_cached(self, mock_get_if_hwaddr):
        network_utils.init('eth0')
        mock_get_if_hwaddr.return_value = 'aa:bb:cc:dd:ee:ff'
        
        # First call
        result1 = network_utils.get_mac()
        # Second call should use cached value
        result2 = network_utils.get_mac()
        
        self.assertEqual(result1, result2)
        # Should only call once due to caching
        mock_get_if_hwaddr.assert_called_once()

    @patch('network_utils.get_if_hwaddr')
    def test_get_mac_all_zeros(self, mock_get_if_hwaddr):
        network_utils.init('eth0')
        mock_get_if_hwaddr.return_value = '00:00:00:00:00:00'
        result = network_utils.get_mac()
        self.assertIsNone(result)

    def test_get_mac_without_interface(self):
        result = network_utils.get_mac()
        self.assertIsNone(result)


class TestGetHostname(unittest.TestCase):
    def setUp(self):
        network_utils._detected_hostname = None

    @patch('socket.gethostname')
    def test_get_hostname(self, mock_gethostname):
        mock_gethostname.return_value = 'test-sensor'
        result = network_utils.get_hostname()
        self.assertEqual(result, 'test-sensor')
        mock_gethostname.assert_called_once()

    @patch('socket.gethostname')
    def test_get_hostname_cached(self, mock_gethostname):
        mock_gethostname.return_value = 'test-sensor'
        
        # First call
        result1 = network_utils.get_hostname()
        # Second call should use cached value
        result2 = network_utils.get_hostname()
        
        self.assertEqual(result1, result2)
        # Should only call once due to caching
        mock_gethostname.assert_called_once()


if __name__ == '__main__':
    unittest.main()
