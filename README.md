# Easy Net Visibility
**Scanning agent and dashboard for visibility to all the services running on the network**

## Description

The easy net visibility allows to view all the devices on the network on a central location

There are two main components:
1. A server - the server-side component
2. A sensor - scans the network and provide the information to the server

Both components are now containerized so it can be easily be deployed.
The sensor will use `nmap` to scan for devices on the network and to identify the open ports on each device.
Optionally, the sensor can also integrate with **Fortigate firewalls** to pull device information directly from the firewall's device database (Assets API), with fallback to ARP and DHCP tables if needed.
The server component is based on `Django` and can be configured to use an external or internal DB.

This was originally based on the open-source SweedSecurity project. Here is a list of some of the changes:
1. Removed any component of IDS system
2. Implmenented on containers
3. Server Implemented on Django
4. Better UI for large number of devices

## Features

- Network device scanning and monitoring
- Port scanning and service detection
- **Fortigate firewall integration** for device discovery
- Web-based dashboard for device visibility
- **Pushover notifications** for real-time alerts:
  - New device detection
  - Gateway timeout alerts
  - Device offline notifications (optional)

For detailed Pushover configuration, see [PUSHOVER.md](PUSHOVER.md).

## Installation:

### For the server –
The server was tested on `X86-X64` `CoreOS` on `GCP` (using a micro instance!)

To deploy it:
1.	Build the docker from the sources (Base directory `/easyNetVisibility/server/server_django`)
2.	Create the directory for the "conf" volume mapping and update the settings.json there
3.	Create the directory for the "db" volume mapping (if using local DB)
4.	Run using the following command:

```
docker run -d --restart=always  \
    -p 8000:8000 \
    --volume="/opt/easy_net_visibility/conf:/opt/app/easy_net_visibility/conf:ro" \
    --volume="/opt/easy_net_visibility/db:/opt/app/easy_net_visibility/db:rw" \
     -e DJANGO_SUPERUSER_USERNAME=[ADMIN_USER] \
     -e DJANGO_SUPERUSER_PASSWORD=[SECRET_PASSWORD] \
     -e DJANGO_SUPERUSER_EMAIL=[ADMIN_EMAIL] \
    --name=server \
    [SELECTED_TAG_NAME]
   ``` 
    
You can also deploy a reverse proxy to secure the connection (to use HTTPS)
See example configuration under /easyNetVisibility/server/httpd_proxy_conf directory

### For the sensor -
Sensor tested on `X86` (`Minnow board`) and on `Raspberry PI` (Both `Raspbian` and `Yocto`) 

To deploy it:
1.	Build the docker from the sources (Base directory `easyNetVisibility/client`)
2.	Create a directory for the "conf" and update the config.ini file
3.	Run using the following command:

```
docker run \
  -d \
  --restart=always \
  --name=sensor \
  --hostname=sharefs \
  --net=host \
  -v /opt/easynetvisibility:/opt/sensor/config \
[SELECTED_TAG_NAME]
```


After the deployment the sensor will immediately start scanning for devices and feeding the information to the server.

### Fortigate Firewall Integration

The sensor can optionally integrate with Fortigate firewalls to discover devices using FortiGate's built-in **Assets** view (user device database). This provides comprehensive device information including hostnames, IP addresses, MAC addresses, and OS detection. Falls back to ARP and DHCP tables if the Assets API is unavailable.

#### Configuration

To enable Fortigate integration, update the `config.ini` file with the following settings:

```ini
[Fortigate]
# Set enabled to True to enable Fortigate integration
enabled=True
# Fortigate firewall host (e.g., https://192.168.1.1)
host=https://192.168.1.1
# Fortigate API key for authentication
apiKey=your_api_key_here
# Validate SSL certificate (set to False for self-signed certificates)
validateSSL=False
```

#### Requirements

- Fortigate firewall with REST API enabled (FortiOS 5.6+)
- API key with appropriate permissions (read access to user device monitoring)
- Network connectivity from sensor to Fortigate management interface

#### Creating a Fortigate API Key

To create an API key in FortiGate:
1. Log in to the FortiGate web interface
2. Go to **System** > **Administrators**
3. Click **Create New** > **REST API Admin**
4. Set a name for the API user
5. Configure permissions (minimum: read access to system monitoring and user device data)
6. Click **OK** and copy the generated API key
7. Store the API key securely - it cannot be retrieved later

#### How It Works

When enabled, the sensor will:
1. **Primary method**: Query the FortiGate user device database via `/api/v2/monitor/user/device` (Assets view)
   - Provides comprehensive device information: hostname, IP, MAC, OS name
   - More efficient than polling multiple endpoints
2. **Fallback method**: If Assets API returns no results, falls back to:
   - Query the Fortigate ARP table via `/api/v2/monitor/system/arp`
   - Query the DHCP lease table via `/api/v2/monitor/system/dhcp`
3. Combine and normalize the device information
4. Send discovered devices to the server every 10 minutes

The Fortigate integration runs in parallel with nmap scanning, providing complementary device discovery methods.

## Development and Testing

### Running Tests Locally

The project includes comprehensive unit tests for both server and client components. **Test files are stored in separate `tests/` directories and are not included in production Docker images.**

#### Server Tests (Django)

To run the Django server tests:

```bash
cd easyNetVisibility/server/server_django

# Install dependencies
pip install -r requirements.txt

# Run all tests (from the server_django directory)
cd easy_net_visibility
python manage.py test

# Run specific test modules
python manage.py test tests.test_validators
python manage.py test tests.test_sensor_model
python manage.py test easy_net_visibility_server.tests

# Run with verbosity
python manage.py test --verbosity=2
```

#### Client Tests (Python/Pytest)

To run the client sensor tests:

```bash
cd easyNetVisibility/client

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-mock

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_network_utils.py -v
pytest tests/test_server_api.py -v
pytest tests/test_nmap.py -v
pytest tests/test_fortigate.py -v
```

### Continuous Integration

Tests are automatically run via GitHub Actions on every push and pull request. The CI pipeline:

1. Runs Django server tests (152 tests)
2. Runs client sensor tests (63 tests: 42 original + 21 Fortigate)
3. Reports test results (215 tests total: 152 server + 63 client)

You can view the test results in the Actions tab of the GitHub repository.

### Test Coverage

The test suite covers:

**Server Components:**
- Device, Port, and Sensor models
- API views (CSRF, device/port CRUD, batch operations)
- Validators (MAC address, IP address, hostname, URL)
- Authentication and permissions
- Error handling and edge cases

**Client Components:**
- Network utilities (IP/MAC detection, network interfaces)
- Server API client (authentication, CSRF, HTTP operations)
- Nmap integration (ping sweep, port scanning, XML parsing)
- Fortigate integration (Assets API, user device database, ARP/DHCP fallback, device discovery)
- Error handling and edge cases

