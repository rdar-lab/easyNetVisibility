import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import router_generic


class TestGenericRouterInit(unittest.TestCase):
    def test_init_sets_credentials(self):
        """Test that init properly sets connection parameters"""
        router_generic.init('http://192.168.1.1', 'admin', 'test_password', False)
        
        self.assertEqual(router_generic._router_host, 'http://192.168.1.1')
        self.assertEqual(router_generic._router_username, 'admin')
        self.assertEqual(router_generic._router_password, 'test_password')
        self.assertEqual(router_generic._validate_ssl, False)


class TestGenericRouterDHCPLeases(unittest.TestCase):
    def setUp(self):
        router_generic.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('router_generic._make_request')
    def test_get_dhcp_leases_table_format(self, mock_request):
        """Test successful DHCP leases retrieval with HTML table format"""
        mock_request.return_value = '''
        <table>
        <tr><td>device1</td><td>AA:BB:CC:DD:EE:FF</td><td>192.168.1.10</td></tr>
        <tr><td>device2</td><td>00:11:22:33:44:55</td><td>192.168.1.20</td></tr>
        </table>
        '''
        
        result = router_generic.get_dhcp_leases()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['hostname'], 'device1')
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')
    
    @patch('router_generic._make_request')
    def test_get_dhcp_leases_failure(self, mock_request):
        """Test DHCP leases retrieval failure"""
        mock_request.side_effect = Exception("Connection error")
        
        result = router_generic.get_dhcp_leases()
        
        # Should return empty list on error
        self.assertEqual(result, [])


class TestGenericRouterConnectedDevices(unittest.TestCase):
    def setUp(self):
        router_generic.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('router_generic._make_request')
    def test_get_connected_devices_success(self, mock_request):
        """Test successful connected devices retrieval"""
        mock_request.return_value = '''
        <div>192.168.1.10 AA:BB:CC:DD:EE:FF</div>
        <div>192.168.1.20 00:11:22:33:44:55</div>
        '''
        
        result = router_generic.get_connected_devices()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')


class TestGenericRouterDiscoverDevices(unittest.TestCase):
    def setUp(self):
        router_generic.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('router_generic.get_connected_devices')
    @patch('router_generic.get_dhcp_leases')
    def test_discover_devices_from_dhcp_only(self, mock_dhcp, mock_connected):
        """Test device discovery from DHCP leases only"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'},
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'server1'}
        ]
        mock_connected.return_value = []
        
        result = router_generic.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
    
    @patch('router_generic.get_connected_devices')
    @patch('router_generic.get_dhcp_leases')
    def test_discover_devices_combined_sources(self, mock_dhcp, mock_connected):
        """Test device discovery combining DHCP and connected devices"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'}
        ]
        mock_connected.return_value = [
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55'}
        ]
        
        result = router_generic.discover_devices()
        
        # Should have 2 unique devices
        self.assertEqual(len(result), 2)
        
        # Device from DHCP should have hostname
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
    
    @patch('router_generic.get_connected_devices')
    @patch('router_generic.get_dhcp_leases')
    def test_discover_devices_empty(self, mock_dhcp, mock_connected):
        """Test device discovery with no devices"""
        mock_dhcp.return_value = []
        mock_connected.return_value = []
        
        result = router_generic.discover_devices()
        
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
