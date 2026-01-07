import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import openwrt


class TestOpenWRTInit(unittest.TestCase):
    def test_init_sets_credentials(self):
        """Test that init properly sets connection parameters"""
        openwrt.init('http://192.168.1.1', 'root', 'test_password', False)
        
        self.assertEqual(openwrt._openwrt_host, 'http://192.168.1.1')
        self.assertEqual(openwrt._openwrt_username, 'root')
        self.assertEqual(openwrt._openwrt_password, 'test_password')
        self.assertEqual(openwrt._validate_ssl, False)


class TestOpenWRTDHCPLeases(unittest.TestCase):
    def setUp(self):
        openwrt.init('http://192.168.1.1', 'root', 'test_password', False)
    
    @patch('openwrt.requests.get')
    def test_get_dhcp_leases_json_format(self, mock_get):
        """Test successful DHCP leases retrieval with JSON format"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'dhcp_leases': [
                {'ipaddr': '192.168.1.10', 'macaddr': 'AA:BB:CC:DD:EE:FF', 'hostname': 'device1'},
                {'ipaddr': '192.168.1.20', 'macaddr': '00:11:22:33:44:55', 'hostname': 'device2'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = openwrt.get_dhcp_leases()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['hostname'], 'device1')
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')
    
    @patch('openwrt.requests.get')
    def test_get_dhcp_leases_failure(self, mock_get):
        """Test DHCP leases retrieval failure"""
        mock_get.side_effect = Exception("Connection error")
        
        result = openwrt.get_dhcp_leases()
        
        # Should return empty list on error
        self.assertEqual(result, [])


class TestOpenWRTDiscoverDevices(unittest.TestCase):
    def setUp(self):
        openwrt.init('http://192.168.1.1', 'root', 'test_password', False)
    
    @patch('openwrt.get_wireless_clients')
    @patch('openwrt.get_dhcp_leases')
    def test_discover_devices_from_dhcp_only(self, mock_dhcp, mock_wireless):
        """Test device discovery from DHCP leases only"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'},
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'server1'}
        ]
        mock_wireless.return_value = []
        
        result = openwrt.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
    
    @patch('openwrt.get_wireless_clients')
    @patch('openwrt.get_dhcp_leases')
    def test_discover_devices_combined_sources(self, mock_dhcp, mock_wireless):
        """Test device discovery combining DHCP and wireless clients"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'}
        ]
        mock_wireless.return_value = [
            {'mac': 'AA:BB:CC:DD:EE:FF'},  # Same device
            {'mac': '00:11:22:33:44:55'}   # New device
        ]
        
        result = openwrt.discover_devices()
        
        # Should have 2 unique devices
        self.assertEqual(len(result), 2)
        
        # Device from DHCP should have hostname
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
    
    @patch('openwrt.get_wireless_clients')
    @patch('openwrt.get_dhcp_leases')
    def test_discover_devices_empty(self, mock_dhcp, mock_wireless):
        """Test device discovery with no devices"""
        mock_dhcp.return_value = []
        mock_wireless.return_value = []
        
        result = openwrt.discover_devices()
        
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
