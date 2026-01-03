# Easy Net Visibility
**Scanning agent and dashboard for visibility to all the services running on the network**

## Description

The easy net visibility allows to view all the devices on the network on a central location

There are two main components:
1. A server - the server-side component
2. A sensor - scans the network and provide the information to the server

Both components are now containerized so it can be easily be deployed.
The sensor will use `nmap` to scan for devices on the network and to identify the open ports on each device.
The server component is based on `Django` and can be configured to use an external or internal DB.

This was originally based on the open-source SweedSecurity project. Here is a list of some of the changes:
1. Removed any component of IDS system
2. Implmenented on containers
3. Server Implemented on Django
4. Better UI for large number of devices

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
```

### Continuous Integration

Tests are automatically run via GitHub Actions on every push and pull request. The CI pipeline:

1. Runs Django server tests (122 tests)
2. Runs client sensor tests (42 tests)
3. Reports test results (164 tests total: 122 server + 42 client)

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
- Error handling and edge cases

