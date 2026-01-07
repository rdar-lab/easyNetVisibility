#!/usr/bin/env python3
"""
Manual test script for DD-WRT router integration.

This script tests the DD-WRT API integration by connecting to a DD-WRT
router and displaying discovered devices.

Usage:
    python test_ddwrt_manual.py --host http://192.168.1.1 --username admin --password PASSWORD [--no-ssl-verify]

Requirements:
    - Access to a DD-WRT router
    - Valid admin credentials
"""

import argparse
import sys
import os
import logging

# Add sensor directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'sensor'))

import ddwrt


def setup_logging():
    """Setup logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_devices(devices):
    """Print discovered devices in a formatted table."""
    if not devices:
        print("\nNo devices discovered.")
        return

    print(f"\n{'='*80}")
    print(f"Discovered {len(devices)} devices:")
    print(f"{'='*80}")
    print(f"{'Hostname':<30} {'IP Address':<15} {'MAC Address':<17} {'Vendor':<15}")
    print(f"{'-'*80}")

    for device in devices:
        hostname = device.get('hostname', 'N/A')
        ip = device.get('ip', 'N/A')
        mac = device.get('mac', 'N/A')
        vendor = device.get('vendor', 'N/A')
        print(f"{hostname:<30} {ip:<15} {mac:<17} {vendor:<15}")

    print(f"{'='*80}\n")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description='Test DD-WRT router API integration'
    )
    parser.add_argument(
        '--host',
        required=True,
        help='DD-WRT router URL (e.g., http://192.168.1.1)'
    )
    parser.add_argument(
        '--username',
        default='admin',
        help='DD-WRT admin username (default: admin)'
    )
    parser.add_argument(
        '--password',
        required=True,
        help='DD-WRT admin password'
    )
    parser.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='Disable SSL certificate verification (use for self-signed certs)'
    )

    args = parser.parse_args()

    setup_logging()

    print("\n" + "="*80)
    print("DD-WRT Integration Test")
    print("="*80)
    print(f"Host: {args.host}")
    print(f"Username: {args.username}")
    print(f"SSL Verification: {'Disabled' if args.no_ssl_verify else 'Enabled'}")
    print("="*80 + "\n")

    try:
        # Initialize DD-WRT integration
        print("Initializing DD-WRT connection...")
        ddwrt.init(
            host=args.host,
            username=args.username,
            password=args.password,
            validate_ssl=not args.no_ssl_verify
        )
        print("✓ Connection initialized successfully\n")

        # Test DHCP leases
        print("Testing DHCP lease retrieval...")
        dhcp_leases = ddwrt.get_dhcp_leases()
        print(f"✓ Retrieved {len(dhcp_leases)} DHCP leases\n")

        # Test ARP table
        print("Testing ARP table retrieval...")
        arp_table = ddwrt.get_arp_table()
        print(f"✓ Retrieved {len(arp_table)} ARP entries\n")

        # Test wireless clients
        print("Testing wireless client retrieval...")
        wireless_clients = ddwrt.get_wireless_clients()
        print(f"✓ Retrieved {len(wireless_clients)} wireless clients\n")

        # Test device discovery
        print("Testing device discovery...")
        devices = ddwrt.discover_devices()
        print(f"✓ Discovered {len(devices)} devices\n")

        # Display results
        print_devices(devices)

        print("✓ All tests completed successfully!")
        return 0

    except Exception as e:
        print(f"\n✗ Error during testing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
