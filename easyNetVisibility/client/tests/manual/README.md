# Manual Testing Scripts for Router Integrations

This directory contains manual testing scripts for each router integration module. These scripts allow you to test router API integrations directly without running the full sensor application.

## Overview

Each test script:
- Uses the same Python classes/modules as the production integration
- Connects to the router using provided credentials
- Tests all API functions (DHCP leases, connected devices, etc.)
- Displays discovered devices in a formatted table
- Reports success or failure with detailed error messages

## Available Test Scripts

1. **test_fortigate_manual.py** - Tests Fortigate firewall integration
2. **test_openwrt_manual.py** - Tests OpenWRT router integration
3. **test_ddwrt_manual.py** - Tests DD-WRT router integration

## Prerequisites

Before running the test scripts, ensure you have:

1. **Python 3.8+** installed
2. **Required Python packages** installed:
   ```bash
   cd /path/to/easyNetVisibility/client
   pip install -r requirements.txt
   ```
3. **Network access** to the router you want to test
4. **Valid credentials** for router access (username/password or API key)

## Usage

### General Format

Each script follows a similar command-line interface:

```bash
python test_<router>_manual.py --host <URL> [--username <user>] --password <pass> [--no-ssl-verify]
```

### Fortigate Firewall

```bash
# Basic usage
python test_fortigate_manual.py \
    --host https://192.168.1.1 \
    --api-key YOUR_API_KEY_HERE

# With self-signed certificate (skip SSL verification)
python test_fortigate_manual.py \
    --host https://192.168.1.1 \
    --api-key YOUR_API_KEY_HERE \
    --no-ssl-verify
```

**Requirements:**
- Fortigate firewall with REST API enabled
- API key with read permissions for monitoring endpoints
- HTTPS access to Fortigate management interface

### OpenWRT Router

```bash
# Basic usage
python test_openwrt_manual.py \
    --host http://192.168.1.1 \
    --username root \
    --password YOUR_PASSWORD

# With custom username
python test_openwrt_manual.py \
    --host http://192.168.1.1 \
    --username admin \
    --password YOUR_PASSWORD
```

**Requirements:**
- OpenWRT router with web interface enabled
- Admin credentials (default username is usually 'root')
- HTTP/HTTPS access to router

### DD-WRT Router

```bash
# Basic usage
python test_ddwrt_manual.py \
    --host http://192.168.1.1 \
    --username admin \
    --password YOUR_PASSWORD

# With HTTPS
python test_ddwrt_manual.py \
    --host https://192.168.1.1 \
    --username admin \
    --password YOUR_PASSWORD \
    --no-ssl-verify
```

**Requirements:**
- DD-WRT router with web interface enabled
- Admin credentials (default username is usually 'admin')
- HTTP/HTTPS access to router


```bash
# Basic usage
python  \
    --host http://192.168.1.1 \
    --username admin \
    --password YOUR_PASSWORD

# With custom settings
python  \
    --host http://10.0.0.1 \
    --username user \
    --password YOUR_PASSWORD
```

## Command-Line Options

### Common Options (All Scripts)

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--host` | Router URL (e.g., http://192.168.1.1) | Yes | - |
| `--password` | Admin password | Yes | - |
| `--no-ssl-verify` | Skip SSL certificate verification | No | False |

### Router-Specific Options

**Fortigate:**
- `--api-key`: API key for authentication (Required)

**OpenWRT, DD-WRT:**
- `--username`: Admin username (Optional, has defaults)

## Output Format

Each test script produces output in this format:

```
================================================================================
<Router Name> Integration Test
================================================================================
Host: http://192.168.1.1
Username: admin
SSL Verification: Disabled
================================================================================

Initializing <Router> connection...
✓ Connection initialized successfully

Testing DHCP lease retrieval...
✓ Retrieved 5 DHCP leases

Testing [additional features]...
✓ Retrieved X items

Testing device discovery...
✓ Discovered 8 devices

================================================================================
Discovered 8 devices:
================================================================================
Hostname                       IP Address      MAC Address       Vendor
--------------------------------------------------------------------------------
laptop1                        192.168.1.10    AABBCCDDEEFF     Unknown
server1                        192.168.1.20    001122334455     Unknown
phone-wifi                     192.168.1.30    112233445566     Unknown
...
================================================================================

✓ All tests completed successfully!
```

## Troubleshooting

### Connection Errors

**Problem:** `Connection refused` or `Timeout`

**Solutions:**
- Verify the router IP address is correct
- Ensure network connectivity: `ping 192.168.1.1`
- Check if the router's web interface is enabled
- Verify firewall rules allow access from your machine

### Authentication Errors

**Problem:** `401 Unauthorized` or authentication failures

**Solutions:**
- Double-check username and password
- Ensure admin account is not locked
- For Fortigate: Verify API key is valid and not expired
- Check if admin access is restricted by IP address

### SSL Certificate Errors

**Problem:** SSL certificate verification errors

**Solutions:**
- Use `--no-ssl-verify` flag for self-signed certificates
- For production: Install valid SSL certificates on the router
- Ensure you're using `https://` in the host URL for HTTPS

### No Devices Discovered

**Problem:** Test completes but shows 0 devices

**Solutions:**
- Verify devices are actually connected to the router
- Check if DHCP server is enabled
- Try accessing the router's web interface manually to see if devices appear there
- Check sensor logs for detailed error messages
- Ensure API permissions are sufficient (especially for Fortigate)

### Module Import Errors

**Problem:** `ImportError` or `ModuleNotFoundError`

**Solutions:**
- Install required packages: `pip install -r requirements.txt`
- Ensure you're running from the correct directory
- Check Python version (requires 3.8+)

## Security Notes

1. **Never commit credentials** to version control
2. **Use SSL verification** in production environments (`--no-ssl-verify` should only be used for testing with self-signed certificates)
3. **Store API keys securely** (use environment variables or secure key management)
4. **Limit API permissions** to read-only access where possible
5. **Monitor API access logs** on your router for suspicious activity

## Integration with Production

These test scripts use the **exact same code** as the production sensor integration:

- `test_fortigate_manual.py` uses `/sensor/fortigate.py`
- `test_openwrt_manual.py` uses `/sensor/openwrt.py`
- `test_ddwrt_manual.py` uses `/sensor/ddwrt.py`
- `` uses `/sensor/bezeq.py`
- `` uses `/sensor/partner.py`

This ensures that:
- Testing reflects actual production behavior
- Bug fixes in test scripts benefit production code
- Validation is consistent between manual testing and automated sensor operation

## Contributing

When adding a new router integration:

1. Create the integration module in `/sensor/<router>.py`
2. Create a corresponding test script `test_<router>_manual.py` following the existing patterns
3. Add documentation to this README
4. Test thoroughly with actual hardware before submitting

## Support

For issues or questions:
- Check the main project [README.md](../../../../README.md)
- Review [ARCHITECTURE.md](../../../../ARCHITECTURE.md) for system design
- Open an issue on the GitHub repository with:
  - Router model and firmware version
  - Command you ran (with credentials redacted)
  - Full error output
  - Network configuration details
