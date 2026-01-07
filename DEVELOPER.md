# Developer Guide

This guide provides instructions for setting up and running Easy Net Visibility locally for development purposes, without Docker.

**Related Documentation**: [README.md](README.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [API.md](API.md) | [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Python 3.11 recommended)
- **pip** (Python package manager)
- **virtualenv** or **venv** (for creating isolated Python environments)
- **nmap** (for sensor network scanning)
- **Git** (for version control)

### Installing Prerequisites

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv nmap git
```

**macOS** (using Homebrew):
```bash
brew install python nmap git
```

**Windows**:
- Install Python from [python.org](https://www.python.org/)
- Install nmap from [nmap.org](https://nmap.org/download.html)
- Install Git from [git-scm.com](https://git-scm.com/)

---

## Repository Setup

1. **Clone the repository**:
```bash
git clone https://github.com/rdar-lab/easyNetVisibility.git
cd easyNetVisibility
```

2. **Verify the structure**:
```bash
ls -la
# You should see:
# - easyNetVisibility/    (main source code)
# - README.md
# - DEVELOPER.md         (this file)
# - etc.
```

---

## Running Tests Locally

The project includes comprehensive test suites for both server and client components.

### Server Tests

The server uses Django's test framework with 155 automated tests.

**Setup and run server tests**:
```bash
# Navigate to the server directory
cd easyNetVisibility/server/server_django

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all server tests
cd easy_net_visibility
python manage.py test --verbosity=2
```

### Client Tests

The client uses Python's unittest framework with 82 automated tests.

**Setup and run client tests**:
```bash
# Navigate to the client directory
cd easyNetVisibility/client

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all client tests
python -m unittest discover tests/ -v
```

### All Tests

To run both server and client tests (from repository root):

```bash
# Run server tests
cd easyNetVisibility/server/server_django
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd easy_net_visibility
python manage.py test --verbosity=2
cd ../../../..

# Run client tests
cd easyNetVisibility/client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m unittest discover tests/ -v
cd ../..
```

---

## Starting the Server Locally

### Server Setup

1. **Navigate to the server directory**:
```bash
cd easyNetVisibility/server/server_django
```

2. **Create and activate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create configuration directory**:
```bash
cd easy_net_visibility
mkdir -p conf
mkdir -p db
```

5. **Create development settings**:
```bash
cat > conf/settings.json << 'EOF'
{
  "DATABASES": {
    "default": {
      "ENGINE": "django.db.backends.sqlite3",
      "NAME": "db/db.sqlite3"
    }
  },
  "SECRET_KEY": "dev-secret-key-change-in-production",
  "DEBUG": "True",
  "STATIC_ROOT": "static"
}
EOF
```

**Note**: For production, generate a secure SECRET_KEY:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

6. **Initialize the database**:
```bash
python manage.py migrate
```

7. **Create a superuser account**:
```bash
python manage.py createsuperuser
# Follow the prompts to set username, email, and password
```

8. **Collect static files** (optional, for admin interface styling):
```bash
python manage.py collectstatic --no-input
```

### Running the Server

Start the Django development server:

```bash
python manage.py runserver 0.0.0.0:8000
```

The server will start and display:
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

**Note**: The development server automatically reloads when you make code changes.

### Accessing the Dashboard

Open your web browser and navigate to:
- **Dashboard**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/

Login with the superuser credentials you created during setup.

---

## Starting the Sensor Locally

### Sensor Setup

1. **Navigate to the sensor directory**:
```bash
cd easyNetVisibility/client
```

2. **Create and activate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create/update sensor configuration**:
```bash
cd sensor
cat > config/config.ini << 'EOF'
[ServerAPI]
serverURL=http://localhost:8000
serverUsername=admin
serverPassword=your_password_here
validateServerIdentity=False

[General]
interface=eth0
EOF
```

**Important Configuration Notes**:
- Replace `your_password_here` with the password of your Django superuser
- Update `interface` to match your network interface (find with `ip addr` or `ifconfig`)
- Common interface names: `eth0`, `ens33`, `wlan0`, `en0`

5. **Find your network interface** (if needed):
```bash
# Linux
ip addr show

# macOS
ifconfig

# Windows
ipconfig
```

### Running the Sensor

**Important**: The sensor requires root/administrator privileges to perform network scanning with nmap.

**Linux/macOS**:
```bash
sudo python sensor.py
```

**Windows** (run Command Prompt as Administrator):
```bash
python sensor.py
```

The sensor will:
1. Load configuration from `config/config.ini`
2. Detect the local network interface
3. Register itself with the server
4. Start scanning the network for devices
5. Report discovered devices to the server

**Expected output**:
```
INFO: Configuration loaded successfully
INFO: Network interface: eth0
INFO: Local IP: 192.168.1.100
INFO: Registering sensor with server
INFO: Sensor registered successfully
INFO: Starting network scan
INFO: Discovered 5 devices
INFO: Reported 5 devices to server
```

**Note**: The sensor runs continuously. Press `Ctrl+C` to stop it.

---

## Inserting Test Data

For development and testing, you can easily populate the database with sample devices and ports.

### Using the Test Data Script

A script is provided to quickly insert test data into the database.

1. **Navigate to the server directory**:
```bash
cd easyNetVisibility/server/server_django/easy_net_visibility
```

2. **Ensure virtual environment is activated**:
```bash
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
```

3. **Run the test data script**:
```bash
python scripts/insert_test_data.py
```

The script will insert:
- 10 sample devices with various IP addresses and MAC addresses
- 13 sample ports across different devices (SSH, HTTP, HTTPS, etc.)
- 2 sample sensors (gateways)

**Sample output**:
```
Creating test devices...
✓ Created device: test-server-1 (192.168.1.100)
✓ Created device: test-server-2 (192.168.1.101)
...
Creating test ports...
✓ Created port: SSH (22/tcp) on test-server-1
✓ Created port: HTTP (80/tcp) on test-server-1
...
Creating test sensors...
✓ Created sensor: sensor-1.local (MAC: AA:BB:CC:DD:EE:01)

Successfully inserted test data:
- 10 devices
- 13 ports
- 2 sensors
```

4. **Verify the data**:
   - Open http://localhost:8000/ in your browser
   - You should see the test devices listed on the dashboard

5. **Clear test data** (if needed):
```bash
python manage.py flush --no-input
python manage.py migrate
python manage.py createsuperuser
```

### Manual Data Insertion

You can also insert data manually using the Django shell or admin interface.

**Using Django shell**:
```bash
python manage.py shell
```

```python
from easy_net_visibility_server.models import Device, Port, Sensor

# Create a device
device = Device.objects.create(
    hostname='myserver.local',
    ip='192.168.1.100',
    mac='00:11:22:33:44:55',
    vendor='Intel Corporate'
)

# Create a port on the device
port = Port.objects.create(
    device=device,
    port_num=22,
    protocol='tcp',
    name='ssh',
    product='OpenSSH',
    version='8.2'
)

# Create a sensor
sensor = Sensor.objects.create(
    mac='AA:BB:CC:DD:EE:FF',
    hostname='sensor1.local'
)

print(f"Created device: {device.name()} with {device.port_set.count()} ports")
```

**Using the admin interface**:
1. Navigate to http://localhost:8000/admin/
2. Login with your superuser credentials
3. Click on "Devices", "Ports", or "Sensors"
4. Click "Add" to create new entries
5. Fill in the form and click "Save"

**Using the API** (with curl):
```bash
# Get CSRF token
CSRF_TOKEN=$(curl -s -u admin:password http://localhost:8000/api/csrf | python3 -c "import sys, json; print(json.load(sys.stdin)['csrfToken'])")

# Add a device
curl -X POST http://localhost:8000/api/devices \
  -u admin:password \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "testdevice.local",
    "ip": "192.168.1.200",
    "mac": "AA:BB:CC:DD:EE:11",
    "vendor": "Test Vendor"
  }'
```

---

## Code Quality Tools

The project includes automated code quality checks.

### Linting and Static Analysis

**Run all checks** (from repository root):
```bash
./check_code.sh
```

This will:
1. Install required tools (flake8, bandit)
2. Run flake8 for style checking (server and client)
3. Run bandit for security analysis (server only)

**Manual linting**:

**Server linting**:
```bash
cd easyNetVisibility/server/server_django
pip install flake8 bandit[toml]

# Style checking
flake8 . --count --max-line-length=200 --show-source --statistics --exclude='*/migrations/*,*/tests/*,*/scripts/*'

# Security analysis
bandit -r . -ll -x "*/migrations/*,*/tests/*"
```

**Client linting**:
```bash
cd easyNetVisibility/client
pip install flake8

# Style checking
flake8 . --count --max-line-length=200 --show-source --statistics --exclude='tests'
```

### Code Style Guidelines

- **Line Length**: Maximum 200 characters
- **Python Version**: Python 3.8+ (3.11 recommended)
- **Framework**: Django 4.x, Django REST Framework
- **Testing**: Django TestCase (server), unittest (client)
- **Documentation**: Docstrings for public APIs

---

## Common Development Tasks

### Making Database Changes

1. **Modify models** in `easy_net_visibility_server/models.py`

2. **Create migrations**:
```bash
python manage.py makemigrations
```

3. **Apply migrations**:
```bash
python manage.py migrate
```

4. **View migration SQL** (optional):
```bash
python manage.py sqlmigrate easy_net_visibility_server 0001
```

### Adding a New API Endpoint

1. **Add view** to `easy_net_visibility_server/views.py`
2. **Add URL pattern** to `easy_net_visibility_server/urls.py`
3. **Add tests** to `easy_net_visibility_server/tests/`
4. **Update API documentation** in `API.md`

### Debugging the Server

1. **Enable DEBUG mode** in `conf/settings.json`:
```json
{
  "DEBUG": "True"
}
```

2. **Add breakpoints** in your code:
```python
import pdb; pdb.set_trace()
```

3. **View logs**:
```bash
# Console output shows all requests and SQL queries in DEBUG mode
python manage.py runserver
```

4. **Use Django shell** for testing:
```bash
python manage.py shell
>>> from easy_net_visibility_server.models import Device
>>> Device.objects.all()
```

### Debugging the Sensor

1. **Add logging** to sensor code:
```python
import logging
_logger = logging.getLogger(__name__)
_logger.info("Debug message here")
```

2. **Run with verbose output**:
```bash
sudo python sensor.py
```

3. **Test individual components**:
```python
# Test network utilities
from sensor.network_utils import get_ip_address
print(get_ip_address('eth0'))

# Test server API
from sensor.server_api import ServerAPI
api = ServerAPI('http://localhost:8000', 'admin', 'password', False)
devices = api.get_devices()
```

---

## Troubleshooting

### Server Issues

**Problem: ModuleNotFoundError when starting server**

Solution: Ensure you're in the correct directory and virtual environment is activated:
```bash
cd easyNetVisibility/server/server_django/easy_net_visibility
source ../venv/bin/activate
pip install -r ../requirements.txt
```

**Problem: Database errors**

Solution: Reset the database:
```bash
rm db/db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

**Problem: Static files not loading**

Solution: Collect static files:
```bash
python manage.py collectstatic --no-input
```

**Problem: Port 8000 already in use**

Solution: Use a different port:
```bash
python manage.py runserver 8001
```

### Sensor Issues

**Problem: Permission denied when running sensor**

Solution: Run with sudo (Linux/macOS):
```bash
sudo python sensor.py
```

Or run Command Prompt as Administrator (Windows).

**Problem: Cannot connect to server**

Solution:
1. Verify server is running: `curl http://localhost:8000/api/csrf`
2. Check config.ini has correct server URL
3. Check credentials are correct

**Problem: No devices discovered**

Solution:
1. Verify nmap is installed: `nmap --version`
2. Check network interface is correct: `ip addr` or `ifconfig`
3. Ensure sensor has network access to target devices
4. Check sensor logs for errors

**Problem: ImportError for sensor modules**

Solution: Ensure you're in the sensor directory with virtual environment activated:
```bash
cd easyNetVisibility/client/sensor
source ../venv/bin/activate
pip install -r ../requirements.txt
```

### Test Issues

**Problem: Tests fail with import errors**

Solution: Install test dependencies and run from correct directory:
```bash
# For server tests
cd easyNetVisibility/server/server_django/easy_net_visibility
pip install -r ../requirements.txt
python manage.py test

# For client tests
cd easyNetVisibility/client
pip install -r requirements.txt
python -m unittest discover tests/ -v
```

**Problem: Database errors during tests**

Solution: Django tests use a separate test database that's created and destroyed automatically. If issues persist, try:
```bash
python manage.py test --keepdb  # Reuse test database
```
