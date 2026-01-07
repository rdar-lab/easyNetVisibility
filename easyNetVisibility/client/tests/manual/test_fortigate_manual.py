#!/usr/bin/env python3
"""
Manual test script for Fortigate router integration.

This script tests the Fortigate API integration by connecting to a Fortigate
firewall and displaying discovered devices.

Usage:
    python test_fortigate_manual.py --host https://192.168.1.1 --api-key YOUR_KEY [--no-ssl-verify]

Requirements:
    - Access to a Fortigate firewall
    - Valid API key with read permissions
"""

import argparse
import sys
import os
import logging

# Add sensor directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'sensor'))

import fortigate


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
        description='Test Fortigate router API integration'
    )
    parser.add_argument(
        '--host',
        required=True,
        help='Fortigate host URL (e.g., https://192.168.1.1)'
    )
    parser.add_argument(
        '--api-key',
        required=True,
        help='Fortigate API key for authentication'
    )
    parser.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='Disable SSL certificate verification (use for self-signed certs)'
    )

    args = parser.parse_args()

    setup_logging()

    print("\n" + "="*80)
    print("Fortigate Integration Test")
    print("="*80)
    print(f"Host: {args.host}")
    print(f"SSL Verification: {'Disabled' if args.no_ssl_verify else 'Enabled'}")
    print("="*80 + "\n")

    try:
        # Initialize Fortigate integration
        print("Initializing Fortigate connection...")
        fortigate.init(
            host=args.host,
            api_key=args.api_key,
            validate_ssl=not args.no_ssl_verify
        )
        print("✓ Connection initialized successfully\n")

        # Test DHCP leases
        print("Testing DHCP lease retrieval...")
        dhcp_leases = fortigate.get_dhcp_leases()
        print(f"✓ Retrieved {len(dhcp_leases)} DHCP leases\n")

        # Test firewall sessions
        print("Testing firewall session retrieval...")
        firewall_sessions = fortigate.get_firewall_sessions()
        print(f"✓ Retrieved {len(firewall_sessions)} firewall sessions\n")

        # Test device discovery
        print("Testing device discovery...")
        devices = fortigate.discover_devices()
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
