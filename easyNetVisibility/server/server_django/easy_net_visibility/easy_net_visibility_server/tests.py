import datetime
from abc import ABC

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Device
from .models import Port
from .views import get_subnet


class TestDeviceModel(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            nickname='TestDevice',
            hostname='testhost',
            ip='192.168.1.2',
            mac='AA:BB:CC:DD:EE:FF',
            vendor='TestVendor',
            first_seen=timezone.now() - datetime.timedelta(days=2),
            last_seen=timezone.now() - datetime.timedelta(hours=1)
        )

    def test_name_returns_nickname(self):
        self.assertEqual(self.device.name(), 'TestDevice')

    def test_online_true(self):
        self.assertTrue(self.device.online())

    def test_first_seen_today_false(self):
        self.assertFalse(self.device.first_seen_today())

    def test_is_hidden_false(self):
        self.assertFalse(self.device.is_hidden())

    def test_str_method(self):
        self.assertIn('TestDevice', str(self.device))
        self.assertIn('192.168.1.2', str(self.device))


class TestSubnetCalculation(TestCase):
    def test_get_subnet_standard_ip(self):
        self.assertEqual(get_subnet('192.168.1.100'), '192.168.1.0/24')
        self.assertEqual(get_subnet('10.0.0.5'), '10.0.0.0/24')
        self.assertEqual(get_subnet('172.16.5.20'), '172.16.5.0/24')

    def test_get_subnet_different_prefix(self):
        self.assertEqual(get_subnet('192.168.1.100', 16), '192.168.0.0/16')
        self.assertEqual(get_subnet('10.0.0.5', 8), '10.0.0.0/8')

    def test_get_subnet_invalid_ip(self):
        self.assertEqual(get_subnet('invalid'), 'unknown')
        self.assertEqual(get_subnet(''), 'unknown')
        self.assertEqual(get_subnet('999.999.999.999'), 'unknown')


class TestPortModel(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            nickname='TestDevice',
            hostname='testhost',
            ip='192.168.1.2',
            mac='AA:BB:CC:DD:EE:11',
            vendor='TestVendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        self.port = Port.objects.create(
            device=self.device,
            port_num=80,
            protocol='TCP',
            name='http',
            product='nginx',
            version='1.18',
            first_seen=timezone.now(),
            last_seen=timezone.now()  # Added last_seen to fix NOT NULL error
        )

    def test_port_num(self):
        self.assertEqual(self.port.port_num, 80)
        self.assertEqual(self.port.device.mac, 'AA:BB:CC:DD:EE:11')


class TestDeviceView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.device = Device.objects.create(
            nickname='ViewDevice',
            hostname='viewhost',
            ip='10.0.0.1',
            mac='AABBCCDDEE22',
            vendor='Vendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        response_content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('ViewDevice', response_content)
        self.assertIn('10.0.0.1', response_content)  # Check if IP is displayed
        self.assertIn('AABBCCDDEE22', response_content)  # Check if MAC is displayed

    def test_home_view_groups_by_subnet(self):
        # Create devices in different subnets
        Device.objects.create(
            nickname='Device1',
            hostname='host1',
            ip='192.168.1.10',
            mac='AABBCCDDEE01',
            vendor='Vendor1',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        Device.objects.create(
            nickname='Device2',
            hostname='host2',
            ip='192.168.1.20',
            mac='AABBCCDDEE02',
            vendor='Vendor2',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        Device.objects.create(
            nickname='Device3',
            hostname='host3',
            ip='192.168.2.10',
            mac='AABBCCDDEE03',
            vendor='Vendor3',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )

        response = self.client.get(reverse('home'))
        response_content = response.content.decode()
        self.assertEqual(response.status_code, 200)

        # Check that subnet headers are present
        self.assertIn('Subnet:', response_content)
        self.assertIn('192.168.1.0/24', response_content)
        self.assertIn('192.168.2.0/24', response_content)

        # Check that devices are displayed
        self.assertIn('Device1', response_content)
        self.assertIn('Device2', response_content)
        self.assertIn('Device3', response_content)

    def test_rename_device(self):
        response = self.client.post(reverse('rename_device'), {
            'device_id': self.device.id,
            'nickname': 'RenamedDevice'
        })
        self.device.refresh_from_db()
        self.assertEqual(self.device.nickname, 'RenamedDevice')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Device updated successfully')

    def test_delete_device(self):
        response = self.client.post(reverse('delete_device'), {
            'device_id': self.device.id
        })
        self.assertFalse(Device.objects.filter(id=self.device.id).exists())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Device deleted successfully')

    def test_delete_device_deletes_ports(self):
        from .models import Device, Port
        # Create device
        device = Device.objects.create(
            nickname='DeleteMe',
            hostname='deleteme-host',
            ip='192.168.1.100',
            mac='AABBCCDDEEDE',
            vendor='TestVendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        # Add ports to device
        Port.objects.create(
            device=device,
            port_num=80,
            protocol='TCP',
            name='http',
            product='nginx',
            version='1.0',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        Port.objects.create(
            device=device,
            port_num=443,
            protocol='TCP',
            name='https',
            product='nginx',
            version='1.0',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        # Confirm device and ports exist
        self.assertEqual(Device.objects.filter(id=device.id).count(), 1)
        self.assertEqual(Port.objects.filter(device=device).count(), 2)
        # Delete device via view
        response = self.client.post(
            reverse('delete_device'),
            {'device_id': device.id}
        )
        self.assertEqual(response.status_code, 200)
        # Confirm device and ports are deleted
        self.assertEqual(Device.objects.filter(id=device.id).count(), 0)
        self.assertEqual(Port.objects.filter(device=device).count(), 0)

    def test_rename_device_flow(self):
        from .models import Device
        # Create a device
        device = Device.objects.create(
            nickname='OldName',
            hostname='rename-host',
            ip='192.168.1.101',
            mac='AABBCCDDEEF1',
            vendor='TestVendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        # Rename the device via the view
        new_nickname = 'NewName'
        response = self.client.post(
            reverse('rename_device'),
            {'device_id': device.id, 'nickname': new_nickname}
        )
        self.assertEqual(response.status_code, 200)
        # Refresh from DB and check nickname
        device.refresh_from_db()
        self.assertEqual(device.nickname, new_nickname)
        # Optionally, check response contains new nickname
        self.assertContains(response, new_nickname)

    def test_delete_device_invalid_id(self):
        # Try to delete a device that does not exist
        invalid_id = 999999
        response = self.client.post(
            reverse('delete_device'),
            {'device_id': invalid_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(id=invalid_id).exists())
        # The response should contain the capitalized warning message
        self.assertContains(response, "Device matching query does not exist")

    def test_rename_device_invalid_id(self):
        # Try to rename a device that does not exist
        invalid_id = 888888
        response = self.client.post(
            reverse('rename_device'),
            {'device_id': invalid_id, 'nickname': 'ShouldNotExist'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(id=invalid_id).exists())
        # The response should contain the capitalized warning message
        self.assertContains(response, "Device matching query does not exist")

    def test_rename_device_without_csrf_token(self):
        """Test that rename_device works without CSRF token when CSRF_PROTECTION_ENABLED is False"""
        # Create a new client without CSRF token
        client = Client(enforce_csrf_checks=True)
        client.login(username='testuser', password='testpass')

        # This should work because CSRF_PROTECTION_ENABLED is False in settings
        response = client.post(reverse('rename_device'), {
            'device_id': self.device.id,
            'nickname': 'NewNameWithoutCSRF'
        })

        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertEqual(self.device.nickname, 'NewNameWithoutCSRF')

    def test_delete_device_without_csrf_token(self):
        """Test that delete_device works without CSRF token when CSRF_PROTECTION_ENABLED is False"""
        # Create a test device for deletion
        device_to_delete = Device.objects.create(
            nickname='DeleteWithoutCSRF',
            hostname='deletehost',
            ip='10.0.0.99',
            mac='AABBCCDDEE99',
            vendor='Vendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )

        # Create a new client without CSRF token
        client = Client(enforce_csrf_checks=True)
        client.login(username='testuser', password='testpass')

        # This should work because CSRF_PROTECTION_ENABLED is False in settings
        response = client.post(reverse('delete_device'), {
            'device_id': device_to_delete.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(id=device_to_delete.id).exists())


class BaseDeviceApiTest(ABC, TestCase):
    def api_post(self, url_name, data, extra=None):
        self.skipTest("Abstract method not implemented")

    def setUp(self):
        if 'BaseDeviceApiTest' in self.__class__.__name__:
            self.skipTest("Abstract method not implemented")

        self.user = User.objects.create_user(username='apiuser', password='apipass')
        self.client = APIClient()
        self.client.login(username='apiuser', password='apipass')
        response = self.client.get(reverse('get_csrf_token'))
        self.csrf_token = response.content.decode()
        self.client.cookies['csrftoken'] = self.csrf_token

    def test_get_csrf_token(self):
        response = self.client.get(reverse('get_csrf_token'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)

    def test_add_device_missing_mac(self):
        payload = {
            'hostname': 'apiHost',
            'ip': '10.0.0.2',
            'vendor': 'ApiVendor',
            'mac': ''
        }
        response = self.api_post('add_device', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Must Supply MAC Address', response.content)

    def test_add_device_invalid_mac(self):
        payload = {
            'hostname': 'apiHost',
            'ip': '10.0.0.2',
            'vendor': 'ApiVendor',
            'mac': 'INVALIDMAC'
        }
        response = self.api_post('add_device', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid MAC Address', response.content)

    def test_add_device_invalid_ip(self):
        payload = {
            'hostname': 'apiHost',
            'ip': '999.999.999.999',
            'vendor': 'ApiVendor',
            'mac': 'AA:BB:CC:DD:EE:03'
        }
        response = self.api_post('add_device', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid IP Address', response.content)

    def test_add_device_invalid_hostname(self):
        payload = {
            'hostname': '!!!invalid!!!',
            'ip': '10.0.0.4',
            'vendor': 'ApiVendor',
            'mac': 'AA:BB:CC:DD:EE:04'
        }
        response = self.api_post('add_device', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid Hostname', response.content)

    def test_add_and_update_device_via_api(self):
        payload1 = {
            'hostname': 'apiHost1',
            'ip': '10.0.0.2',
            'vendor': 'ApiVendor1',
            'mac': 'AA:BB:CC:DD:EE:01'
        }
        payload2 = {
            'hostname': 'apiHost2',
            'ip': '10.0.0.3',
            'vendor': 'ApiVendor2',
            'mac': 'AA:BB:CC:DD:EE:02'
        }
        payload3 = {
            'hostname': 'apiHost1',
            'ip': '10.0.0.99',
            'vendor': 'ApiVendor1',
            'mac': 'AA:BB:CC:DD:EE:01'
        }
        response1 = self.api_post('add_device', payload1)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Device information processed', response1.content)
        response2 = self.api_post('add_device', payload2)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Device information processed', response2.content)
        from .models import Device
        devices = Device.objects.all()
        self.assertEqual(devices.count(), 2)
        macs = set(dev.mac for dev in devices)
        self.assertIn('AABBCCDDEE01', macs)
        self.assertIn('AABBCCDDEE02', macs)
        response3 = self.api_post('add_device', payload3)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Device information processed', response3.content)
        devices = Device.objects.all()
        self.assertEqual(devices.count(), 2)
        dev1 = Device.objects.get(mac='AABBCCDDEE01')
        self.assertEqual(dev1.ip, '10.0.0.99')
        dev2 = Device.objects.get(mac='AABBCCDDEE02')
        self.assertEqual(dev2.ip, '10.0.0.3')

    def test_add_port_missing_mac(self):
        payload = {
            'port': '80',
            'protocol': 'TCP',
            'name': 'http',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'missing mac address', response.content)

    def test_add_port_missing_port(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:05',
            'protocol': 'TCP',
            'name': 'http',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'missing port number', response.content)

    def test_add_port_missing_protocol(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:05',
            'port': '80',
            'name': 'http',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'missing protocol', response.content)

    def test_add_port_missing_name(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:05',
            'port': '80',
            'protocol': 'TCP',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'missing port name', response.content)

    def test_add_port_device_not_found(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:99',
            'port': '80',
            'protocol': 'TCP',
            'name': 'http',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'device not found', response.content)

    def test_sensor_health_missing_mac(self):
        payload = {
            'hostname': 'sensorHost'
        }
        response = self.api_post('sensor_health', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Unknown Sensor MAC', response.content)

    def test_sensor_health_missing_hostname(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:10'
        }
        response = self.api_post('sensor_health', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'unknown sensor Hostname', response.content)

    def test_sensor_health_creates_sensor(self):
        from .models import Sensor
        mac = 'AA:BB:CC:DD:EE:20'
        hostname = 'sensorHostNew'
        payload = {
            'mac': mac,
            'hostname': hostname
        }
        response = self.api_post('sensor_health', payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sensor information updated', response.content)
        sensors = Sensor.objects.filter(mac=mac)
        self.assertEqual(sensors.count(), 1)
        self.assertEqual(sensors[0].hostname, hostname)

    def test_sensor_health_updates_last_seen(self):
        from .models import Sensor
        mac = 'AA:BB:CC:DD:EE:21'
        old_hostname = 'sensorHostOld'
        new_hostname = 'sensorHostUpdated'
        sensor = Sensor.objects.create(
            mac=mac,
            hostname=old_hostname,
            first_seen=timezone.now() - datetime.timedelta(days=1),
            last_seen=timezone.now() - datetime.timedelta(days=1)
        )
        old_last_seen = sensor.last_seen
        payload = {
            'mac': mac,
            'hostname': new_hostname
        }
        response = self.api_post('sensor_health', payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sensor information updated', response.content)
        sensor.refresh_from_db()
        self.assertEqual(sensor.hostname, new_hostname)
        self.assertTrue(sensor.last_seen > old_last_seen)

    def test_add_port_without_device(self):
        payload = {
            'mac': 'AA:BB:CC:DD:EE:99',
            'port': '8080',
            'protocol': 'TCP',
            'name': 'http',
            'version': '1.0',
            'product': 'nginx'
        }
        response = self.api_post('add_port', payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'device not found', response.content)


class TestDeviceApiForm(BaseDeviceApiTest):
    def api_post(self, url_name, data, extra=None):
        if extra is None:
            extra = {}

        url = reverse(url_name)
        return self.client.post(
            url,
            data,
            format='multipart',
            HTTP_X_CSRFTOKEN=self.csrf_token,
            **extra
        )


class TestDeviceApiJson(BaseDeviceApiTest):
    def api_post(self, url_name, data, extra=None):
        if extra is None:
            extra = {}

        url = reverse(url_name)
        # Ensure Accept header is always set to application/json
        headers = {'HTTP_X_CSRFTOKEN': self.csrf_token, 'HTTP_ACCEPT': 'application/json'}
        headers.update(extra)
        return self.client.post(
            url,
            data,
            format='json',
            **headers
        )


class TestAddDevicesApi(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='batchuser', password='batchpass')
        self.client = APIClient()
        self.client.login(username='batchuser', password='batchpass')
        # Get CSRF token for JSON requests
        response = self.client.get(reverse('get_csrf_token'))
        self.csrf_token = response.content.decode()
        self.client.cookies['csrftoken'] = self.csrf_token
        self.url = reverse('add_devices')

    def post_json(self, payload):
        return self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_X_CSRFTOKEN=self.csrf_token,
            HTTP_ACCEPT='application/json'
        )

    def test_only_accepts_json(self):
        # Should fail with multipart
        response = self.client.post(self.url, {'devices': []}, format='multipart', HTTP_X_CSRFTOKEN=self.csrf_token)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Only JSON format supported', response.content)

    def test_batch_add_all_valid(self):
        payload = {
            'devices': [
                {'mac': 'AA:BB:CC:DD:EE:01', 'hostname': 'host1', 'ip': '10.0.0.1', 'vendor': 'V1'},
                {'mac': 'AA:BB:CC:DD:EE:02', 'hostname': 'host2', 'ip': '10.0.0.2', 'vendor': 'V2'}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 2)
        self.assertEqual(len(data['errors']), 0)
        from .models import Device
        self.assertEqual(Device.objects.count(), 2)

    def test_batch_add_some_invalid(self):
        payload = {
            'devices': [
                {'mac': '', 'hostname': 'host1', 'ip': '10.0.0.1', 'vendor': 'V1'},  # missing MAC
                {'mac': 'INVALIDMAC', 'hostname': 'host2', 'ip': '10.0.0.2', 'vendor': 'V2'},  # invalid MAC
                {'mac': 'AA:BB:CC:DD:EE:03', 'hostname': 'host3', 'ip': '999.999.999.999', 'vendor': 'V3'},
                # invalid IP
                {'mac': 'AA:BB:CC:DD:EE:04', 'hostname': '!!!invalid!!!', 'ip': '10.0.0.4', 'vendor': 'V4'},
                # invalid hostname
                {'mac': 'AA:BB:CC:DD:EE:05', 'hostname': 'host5', 'ip': '10.0.0.5', 'vendor': 'V5'}  # valid
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 1)
        self.assertEqual(len(data['errors']), 4)
        error_msgs = [e['error'] for e in data['errors']]
        self.assertTrue(any('Must Supply MAC Address' in msg for msg in error_msgs))
        self.assertTrue(any('Invalid MAC Address' in msg for msg in error_msgs))
        self.assertTrue(any('Invalid IP Address' in msg for msg in error_msgs))
        self.assertTrue(any('Invalid Hostname' in msg for msg in error_msgs))
        from .models import Device
        self.assertEqual(Device.objects.count(), 1)
        self.assertTrue(Device.objects.filter(mac='AABBCCDDEE05').exists())

    def test_batch_add_duplicate_macs(self):
        # Add device first
        Device.objects.create(mac='AABBCCDDEE06', hostname='oldhost', ip='10.0.0.6', vendor='OldVendor',
                              first_seen=datetime.datetime.now(), last_seen=datetime.datetime.now())
        payload = {
            'devices': [
                {'mac': 'AA:BB:CC:DD:EE:06', 'hostname': 'newhost', 'ip': '10.0.0.66', 'vendor': 'NewVendor'}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 1)
        self.assertEqual(len(data['errors']), 0)
        dev = Device.objects.get(mac='AABBCCDDEE06')
        self.assertEqual(dev.hostname, 'newhost')
        self.assertEqual(dev.ip, '10.0.0.66')
        self.assertEqual(dev.vendor, 'NewVendor')

    def test_batch_add_missing_devices_key(self):
        response = self.post_json({'not_devices': []})
        self.assertEqual(response.status_code, 400)
        self.assertIn('devices', response.content.decode())

    def test_batch_add_devices_not_list(self):
        response = self.post_json({'devices': 'notalist'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('must be a list', response.content.decode())

    def test_batch_add_empty_list(self):
        response = self.post_json({'devices': []})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 0)
        self.assertEqual(len(data['errors']), 0)

    def test_batch_add_all_invalid(self):
        payload = {
            'devices': [
                {'mac': '', 'hostname': '', 'ip': '', 'vendor': ''},
                {'mac': 'BADMAC', 'hostname': '', 'ip': '', 'vendor': ''}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 0)
        self.assertEqual(len(data['errors']), 2)


class TestAddPortsApi(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='portuser', password='portpass')
        self.client = APIClient()
        self.client.login(username='portuser', password='portpass')
        response = self.client.get(reverse('get_csrf_token'))
        self.csrf_token = response.content.decode()
        self.client.cookies['csrftoken'] = self.csrf_token
        self.url = reverse('add_ports')
        # Create a device for valid port tests
        self.device = Device.objects.create(
            nickname='PortDevice',
            hostname='porthost',
            ip='10.0.0.10',
            mac='AABBCCDDEE10',
            vendor='PortVendor',
            first_seen=datetime.datetime.now(),
            last_seen=datetime.datetime.now()
        )

    def post_json(self, payload):
        return self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_X_CSRFTOKEN=self.csrf_token,
            HTTP_ACCEPT='application/json'
        )

    def test_only_accepts_json(self):
        response = self.client.post(self.url, {'ports': []}, format='multipart', HTTP_X_CSRFTOKEN=self.csrf_token)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Only JSON format supported', response.content)

    def test_batch_add_all_valid(self):
        payload = {
            'ports': [
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '80', 'protocol': 'TCP', 'name': 'http', 'version': '1.0',
                 'product': 'nginx'},
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '443', 'protocol': 'TCP', 'name': 'https', 'version': '1.0',
                 'product': 'nginx'}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 2)
        self.assertEqual(len(data['errors']), 0)
        self.assertEqual(Port.objects.filter(device=self.device).count(), 2)

    def test_batch_add_some_invalid(self):
        payload = {
            'ports': [
                {'mac': '', 'port': '80', 'protocol': 'TCP', 'name': 'http'},  # missing MAC
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '', 'protocol': 'TCP', 'name': 'http'},  # missing port
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '8080', 'protocol': '', 'name': 'http'},  # missing protocol
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '8081', 'protocol': 'TCP', 'name': ''},  # missing name
                {'mac': 'AA:BB:CC:DD:EE:99', 'port': '8082', 'protocol': 'TCP', 'name': 'http'}  # device not found
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 0)
        self.assertEqual(len(data['errors']), 5)
        error_msgs = [e['error'] for e in data['errors']]
        self.assertTrue(any('missing mac address' in msg for msg in error_msgs))
        self.assertTrue(any('missing port number' in msg for msg in error_msgs))
        self.assertTrue(any('missing protocol' in msg for msg in error_msgs))
        self.assertTrue(any('missing port name' in msg for msg in error_msgs))
        self.assertTrue(any('device not found' in msg for msg in error_msgs))

    def test_batch_add_duplicate_port(self):
        # Add port first
        Port.objects.create(
            device=self.device,
            port_num='8080',
            protocol='TCP',
            name='http',
            product='nginx',
            version='1.0',
            first_seen=datetime.datetime.now(),
            last_seen=datetime.datetime.now()
        )
        payload = {
            'ports': [
                {'mac': 'AA:BB:CC:DD:EE:10', 'port': '8080', 'protocol': 'TCP', 'name': 'http', 'version': '2.0',
                 'product': 'nginx2'}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 1)
        self.assertEqual(len(data['errors']), 0)
        port = Port.objects.get(device=self.device, port_num='8080')
        self.assertEqual(port.version, '2.0')
        self.assertEqual(port.product, 'nginx2')

    def test_batch_add_missing_ports_key(self):
        response = self.post_json({'not_ports': []})
        self.assertEqual(response.status_code, 400)
        self.assertIn('ports', response.content.decode())

    def test_batch_add_ports_not_list(self):
        response = self.post_json({'ports': 'notalist'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('must be a list', response.content.decode())

    def test_batch_add_empty_list(self):
        response = self.post_json({'ports': []})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 0)
        self.assertEqual(len(data['errors']), 0)

    def test_batch_add_all_invalid(self):
        payload = {
            'ports': [
                {'mac': '', 'port': '', 'protocol': '', 'name': ''},
                {'mac': 'AA:BB:CC:DD:EE:99', 'port': '9999', 'protocol': '', 'name': ''}
            ]
        }
        response = self.post_json(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success_count'], 0)
        self.assertEqual(len(data['errors']), 2)
