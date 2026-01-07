#!/usr/bin/env python
"""
Test Data Insertion Script for Easy Net Visibility

This script inserts sample test data into the database for development and testing purposes.
It creates sample devices, ports, and sensors to help with testing the UI and API.

Usage:
    python scripts/insert_test_data.py
"""

import os
import sys
from datetime import datetime, timedelta

import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easy_net_visibility.settings')
django.setup()

from easy_net_visibility_server.models import Device, Port, Sensor


def create_test_devices():
    """Create sample test devices."""
    print("\nCreating test devices...")

    devices_data = [
        {
            'hostname': 'test-server-1',
            'nickname': 'Main Server',
            'ip': '192.168.1.100',
            'mac': '00:11:22:33:44:55',
            'vendor': 'Intel Corporate',
        },
        {
            'hostname': 'test-server-2',
            'nickname': 'Backup Server',
            'ip': '192.168.1.101',
            'mac': '00:11:22:33:44:56',
            'vendor': 'Dell Inc.',
        },
        {
            'hostname': 'test-workstation-1',
            'nickname': 'Dev Workstation',
            'ip': '192.168.1.102',
            'mac': '00:11:22:33:44:57',
            'vendor': 'Hewlett Packard',
        },
        {
            'hostname': 'test-router',
            'nickname': 'Gateway Router',
            'ip': '192.168.1.1',
            'mac': '00:11:22:33:44:58',
            'vendor': 'Cisco Systems',
        },
        {
            'hostname': 'test-printer',
            'nickname': 'Office Printer',
            'ip': '192.168.1.105',
            'mac': '00:11:22:33:44:59',
            'vendor': 'HP',
        },
        {
            'hostname': 'test-nas',
            'nickname': 'File Server',
            'ip': '192.168.1.110',
            'mac': '00:11:22:33:44:5A',
            'vendor': 'Synology',
        },
        {
            'hostname': 'test-camera-1',
            'nickname': 'Security Camera 1',
            'ip': '192.168.1.120',
            'mac': '00:11:22:33:44:5B',
            'vendor': 'Hikvision',
        },
        {
            'hostname': 'test-camera-2',
            'ip': '192.168.1.121',
            'mac': '00:11:22:33:44:5C',
            'vendor': 'Hikvision',
        },
        {
            'hostname': 'test-switch',
            'nickname': 'Core Switch',
            'ip': '192.168.1.2',
            'mac': '00:11:22:33:44:5D',
            'vendor': 'Cisco Systems',
        },
        {
            'hostname': 'test-iot-device',
            'ip': '192.168.1.130',
            'mac': '00:11:22:33:44:5E',
            'vendor': 'Raspberry Pi Foundation',
        },
    ]

    created_devices = []
    now = datetime.now()

    for i, device_data in enumerate(devices_data):
        # Set first_seen to vary from 30 days ago to today
        first_seen = now - timedelta(days=30 - i * 3)
        # Set last_seen to vary from 1 hour ago to now
        last_seen = now - timedelta(hours=i)

        device, created = Device.objects.get_or_create(
            mac=device_data['mac'],
            defaults={
                'hostname': device_data.get('hostname'),
                'nickname': device_data.get('nickname'),
                'ip': device_data['ip'],
                'vendor': device_data.get('vendor'),
                'first_seen': first_seen,
                'last_seen': last_seen,
            }
        )

        if not created:
            # Update existing device
            device.hostname = device_data.get('hostname')
            device.nickname = device_data.get('nickname')
            device.ip = device_data['ip']
            device.vendor = device_data.get('vendor')
            device.last_seen = last_seen
            device.save()

        created_devices.append(device)
        status = "Created" if created else "Updated"
        print(f"  ✓ {status} device: {device_data.get('hostname', 'Unknown')} ({device_data['ip']})")

    return created_devices


def create_test_ports(devices):
    """Create sample test ports on devices."""
    print("\nCreating test ports...")

    ports_data = [
        # Main Server ports
        {
            'device_index': 0,
            'ports': [
                {'port_num': 22, 'protocol': 'tcp', 'name': 'ssh', 'product': 'OpenSSH', 'version': '8.2'},
                {'port_num': 80, 'protocol': 'tcp', 'name': 'http', 'product': 'nginx', 'version': '1.18.0'},
                {'port_num': 443, 'protocol': 'tcp', 'name': 'https', 'product': 'nginx', 'version': '1.18.0'},
            ]
        },
        # Backup Server ports
        {
            'device_index': 1,
            'ports': [
                {'port_num': 22, 'protocol': 'tcp', 'name': 'ssh', 'product': 'OpenSSH', 'version': '8.4'},
                {'port_num': 3306, 'protocol': 'tcp', 'name': 'mysql', 'product': 'MySQL', 'version': '8.0.26'},
            ]
        },
        # Dev Workstation ports
        {
            'device_index': 2,
            'ports': [
                {'port_num': 22, 'protocol': 'tcp', 'name': 'ssh', 'product': 'OpenSSH', 'version': '8.2'},
            ]
        },
        # Router ports
        {
            'device_index': 3,
            'ports': [
                {'port_num': 80, 'protocol': 'tcp', 'name': 'http', 'product': 'Cisco IOS', 'version': '15.1'},
                {'port_num': 443, 'protocol': 'tcp', 'name': 'https', 'product': 'Cisco IOS', 'version': '15.1'},
            ]
        },
        # File Server ports
        {
            'device_index': 5,
            'ports': [
                {'port_num': 445, 'protocol': 'tcp', 'name': 'microsoft-ds', 'product': 'Samba', 'version': '4.13'},
                {'port_num': 548, 'protocol': 'tcp', 'name': 'afp', 'product': 'netatalk', 'version': '3.1'},
                {'port_num': 5000, 'protocol': 'tcp', 'name': 'http', 'product': 'Synology DSM', 'version': '7.0'},
            ]
        },
        # Core Switch ports
        {
            'device_index': 8,
            'ports': [
                {'port_num': 23, 'protocol': 'tcp', 'name': 'telnet', 'product': 'Cisco IOS', 'version': '15.2'},
                {'port_num': 80, 'protocol': 'tcp', 'name': 'http', 'product': 'Cisco IOS', 'version': '15.2'},
            ]
        },
    ]

    created_count = 0
    now = datetime.now()

    for port_group in ports_data:
        device = devices[port_group['device_index']]

        for port_data in port_group['ports']:
            # Set first_seen to 7 days ago
            first_seen = now - timedelta(days=7)
            # Set last_seen to 30 minutes ago
            last_seen = now - timedelta(minutes=30)

            port, created = Port.objects.get_or_create(
                device=device,
                port_num=port_data['port_num'],
                protocol=port_data.get('protocol', 'tcp'),
                defaults={
                    'name': port_data.get('name'),
                    'product': port_data.get('product'),
                    'version': port_data.get('version'),
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                }
            )

            if not created:
                # Update existing port
                port.name = port_data.get('name')
                port.product = port_data.get('product')
                port.version = port_data.get('version')
                port.last_seen = last_seen
                port.save()

            created_count += 1
            status = "Created" if created else "Updated"
            print(
                f"  ✓ {status} port: {port_data.get('name', 'unknown')} ({port_data['port_num']}/{port_data.get('protocol', 'tcp')}) on {device.hostname}")

    return created_count


def create_test_sensors():
    """Create sample test sensors."""
    print("\nCreating test sensors...")

    sensors_data = [
        {
            'mac': 'AA:BB:CC:DD:EE:01',
            'hostname': 'sensor-1.local',
        },
        {
            'mac': 'AA:BB:CC:DD:EE:02',
            'hostname': 'sensor-2.local',
        },
    ]

    created_sensors = []
    now = datetime.now()

    for i, sensor_data in enumerate(sensors_data):
        # Set first_seen to 10 days ago
        first_seen = now - timedelta(days=10)
        # Set last_seen to 5 minutes ago
        last_seen = now - timedelta(minutes=5)

        sensor, created = Sensor.objects.get_or_create(
            mac=sensor_data['mac'],
            defaults={
                'hostname': sensor_data['hostname'],
                'first_seen': first_seen,
                'last_seen': last_seen,
            }
        )

        if not created:
            # Update existing sensor
            sensor.hostname = sensor_data['hostname']
            sensor.last_seen = last_seen
            sensor.save()

        created_sensors.append(sensor)
        status = "Created" if created else "Updated"
        print(f"  ✓ {status} sensor: {sensor_data['hostname']} (MAC: {sensor_data['mac']})")

    return created_sensors


def main():
    """Main function to insert all test data."""
    print("=" * 60)
    print("Easy Net Visibility - Test Data Insertion")
    print("=" * 60)

    try:
        # Create test devices
        devices = create_test_devices()

        # Create test ports
        port_count = create_test_ports(devices)

        # Create test sensors
        sensors = create_test_sensors()

        # Summary
        print("\n" + "=" * 60)
        print("Successfully inserted test data:")
        print(f"  - {len(devices)} devices")
        print(f"  - {port_count} ports")
        print(f"  - {len(sensors)} sensors")
        print("=" * 60)
        print("\nYou can now access the dashboard at http://localhost:8000/")
        print("to view the test data.")
        print("\nTo clear all data, run:")
        print("  python manage.py flush --no-input")
        print("  python manage.py migrate")

    except Exception as e:
        print(f"\n❌ Error inserting test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
