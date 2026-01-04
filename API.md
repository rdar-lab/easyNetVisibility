# Easy Net Visibility - API Documentation

**Related Documentation**: [README.md](README.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [CONTRIBUTING.md](CONTRIBUTING.md) | [PUSHOVER.md](PUSHOVER.md)

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [CSRF Protection](#csrf-protection)
- [Response Formats](#response-formats)
- [API Endpoints](#api-endpoints)
  - [CSRF Token](#csrf-token)
  - [Devices](#devices)
  - [Ports](#ports)
  - [Sensors](#sensors)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Client Examples](#client-examples)

## Overview

The Easy Net Visibility server provides a RESTful API for managing network devices, ports, and sensors. All API endpoints require authentication and use JSON for request/response data.

**Base URL**: `http://your-server:8000/api` (or `https://` for secure deployments)

**Content Type**: `application/json`

**Authentication**: HTTP Basic Auth

## Authentication

All API requests require HTTP Basic Authentication using Django user credentials.

### Basic Auth Format

```http
GET /api/devices HTTP/1.1
Host: server:8000
Authorization: Basic base64(username:password)
```

### cURL Example

```bash
curl -u username:password http://server:8000/api/devices
```

### Python Example

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('username', 'password')
response = requests.get('http://server:8000/api/devices', auth=auth)
```

### JavaScript Example

```javascript
const auth = btoa('username:password');
fetch('http://server:8000/api/devices', {
  headers: {
    'Authorization': `Basic ${auth}`
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## CSRF Protection

POST, PUT, and DELETE requests require a CSRF token for protection against Cross-Site Request Forgery attacks.

### Obtaining a CSRF Token

**Endpoint**: `GET /api/csrf`

**Request**:
```bash
curl -u username:password http://server:8000/api/csrf
```

**Response**:
```json
{
  "csrfToken": "long-random-token-string-here"
}
```

### Using CSRF Token

Include the token in the `X-CSRFToken` header for state-changing requests:

```bash
curl -X POST http://server:8000/api/devices \
  -u username:password \
  -H "X-CSRFToken: long-random-token-string" \
  -H "Content-Type: application/json" \
  -d '{"mac":"00:11:22:33:44:55","ip":"192.168.1.100"}'
```

## Response Formats

### Success Responses

**Single Object** (200 OK):
```json
{
  "id": 1,
  "hostname": "server.local",
  "ip": "192.168.1.100",
  "mac": "00:11:22:33:44:55",
  "vendor": "Intel Corporate",
  "first_seen": "2024-01-01T10:00:00Z",
  "last_seen": "2024-01-04T15:30:00Z"
}
```

**List of Objects** (200 OK):
```json
[
  {
    "id": 1,
    "hostname": "server1.local",
    ...
  },
  {
    "id": 2,
    "hostname": "server2.local",
    ...
  }
]
```

**Creation Success** (201 Created):
```json
{
  "id": 123,
  "message": "Device created successfully"
}
```

**Update Success** (200 OK):
```json
{
  "message": "Device updated successfully"
}
```

**Deletion Success** (200 OK):
```json
{
  "message": "Device deleted successfully"
}
```

### Error Responses

**Bad Request** (400):
```json
{
  "error": "Invalid MAC address format"
}
```

**Validation Error** (400):
```json
{
  "error": "mac: Invalid MAC Address; ip: Invalid IP Address"
}
```

**Unauthorized** (401):
```json
{
  "error": "Authentication required"
}
```

**Not Found** (404):
```json
{
  "error": "Device not found"
}
```

**Server Error** (500):
```json
{
  "error": "Internal server error"
}
```

## API Endpoints

### CSRF Token

#### Get CSRF Token

Obtain a CSRF token for state-changing requests.

**Endpoint**: `GET /api/csrf`

**Authentication**: Required

**Request**:
```bash
curl -u admin:password http://server:8000/api/csrf
```

**Response** (200 OK):
```json
{
  "csrfToken": "iB9qF4nX7mK2pL8sR3vT5uW1yZ6cE0dG"
}
```

---

### Devices

#### List All Devices

Retrieve a list of all discovered devices.

**Endpoint**: `GET /api/devices`

**Authentication**: Required

**Query Parameters**: None

**Request**:
```bash
curl -u admin:password http://server:8000/api/devices
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "nickname": "Main Server",
    "hostname": "server.local",
    "ip": "192.168.1.100",
    "mac": "00:11:22:33:44:55",
    "vendor": "Intel Corporate",
    "first_seen": "2024-01-01T10:00:00Z",
    "last_seen": "2024-01-04T15:30:00Z",
    "online": true
  },
  {
    "id": 2,
    "nickname": null,
    "hostname": "workstation.local",
    "ip": "192.168.1.101",
    "mac": "00:11:22:33:44:66",
    "vendor": "Dell Inc.",
    "first_seen": "2024-01-02T08:15:00Z",
    "last_seen": "2024-01-04T14:20:00Z",
    "online": true
  }
]
```

**Fields**:
- `id` (int): Unique device identifier
- `nickname` (string|null): User-assigned name
- `hostname` (string|null): DNS hostname
- `ip` (string): IP address
- `mac` (string): MAC address (unique)
- `vendor` (string|null): Vendor from MAC OUI lookup
- `first_seen` (datetime): First detection timestamp
- `last_seen` (datetime): Last detection timestamp
- `online` (boolean): True if seen in last 6 hours

---

#### Get Single Device

Retrieve details for a specific device.

**Endpoint**: `GET /api/devices/{device_id}`

**Authentication**: Required

**Path Parameters**:
- `device_id` (int): Device ID

**Request**:
```bash
curl -u admin:password http://server:8000/api/devices/1
```

**Response** (200 OK):
```json
{
  "id": 1,
  "nickname": "Main Server",
  "hostname": "server.local",
  "ip": "192.168.1.100",
  "mac": "00:11:22:33:44:55",
  "vendor": "Intel Corporate",
  "first_seen": "2024-01-01T10:00:00Z",
  "last_seen": "2024-01-04T15:30:00Z",
  "online": true,
  "ports": [
    {
      "id": 1,
      "port_num": 22,
      "protocol": "tcp",
      "name": "ssh",
      "product": "OpenSSH",
      "version": "8.2"
    },
    {
      "id": 2,
      "port_num": 80,
      "protocol": "tcp",
      "name": "http",
      "product": "nginx",
      "version": "1.18"
    }
  ]
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Device not found"
}
```

---

#### Add Device

Create a new device or update if MAC address exists.

**Endpoint**: `POST /api/devices`

**Authentication**: Required

**CSRF**: Required

**Request Body**:
```json
{
  "hostname": "newdevice.local",
  "ip": "192.168.1.102",
  "mac": "00:11:22:33:44:77",
  "vendor": "Raspberry Pi Foundation"
}
```

**Required Fields**:
- `mac` (string): MAC address (format: XX:XX:XX:XX:XX:XX)
- `ip` (string): IP address

**Optional Fields**:
- `hostname` (string): Device hostname
- `vendor` (string): Vendor name
- `nickname` (string): User-assigned name

**Request**:
```bash
curl -X POST http://server:8000/api/devices \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "newdevice.local",
    "ip": "192.168.1.102",
    "mac": "00:11:22:33:44:77",
    "vendor": "Raspberry Pi Foundation"
  }'
```

**Response** (201 Created):
```json
{
  "id": 3,
  "message": "Device created successfully"
}
```

**Response if device exists** (200 OK):
```json
{
  "id": 3,
  "message": "Device updated successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "mac: Invalid MAC Address; ip: Invalid IP Address"
}
```

---

#### Batch Add Devices

Create or update multiple devices in a single request.

**Endpoint**: `POST /api/devices/batch`

**Authentication**: Required

**CSRF**: Required

**Request Body**:
```json
[
  {
    "hostname": "device1.local",
    "ip": "192.168.1.103",
    "mac": "00:11:22:33:44:88"
  },
  {
    "hostname": "device2.local",
    "ip": "192.168.1.104",
    "mac": "00:11:22:33:44:99"
  }
]
```

**Request**:
```bash
curl -X POST http://server:8000/api/devices/batch \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '[
    {"hostname": "device1.local", "ip": "192.168.1.103", "mac": "00:11:22:33:44:88"},
    {"hostname": "device2.local", "ip": "192.168.1.104", "mac": "00:11:22:33:44:99"}
  ]'
```

**Response** (200 OK):
```json
{
  "message": "Batch operation completed",
  "created": 2,
  "updated": 0,
  "errors": 0
}
```

**Response with errors**:
```json
{
  "message": "Batch operation completed with errors",
  "created": 1,
  "updated": 0,
  "errors": 1,
  "error_details": [
    {
      "device": {"mac": "invalid-mac"},
      "error": "Invalid MAC address format"
    }
  ]
}
```

---

#### Update Device

Update an existing device.

**Endpoint**: `PUT /api/devices/{device_id}`

**Authentication**: Required

**CSRF**: Required

**Path Parameters**:
- `device_id` (int): Device ID

**Request Body** (partial update supported):
```json
{
  "nickname": "Production Server",
  "hostname": "prod-server.local"
}
```

**Request**:
```bash
curl -X PUT http://server:8000/api/devices/1 \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Production Server"}'
```

**Response** (200 OK):
```json
{
  "message": "Device updated successfully"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Device not found"
}
```

---

#### Delete Device

Delete a device and all associated ports.

**Endpoint**: `DELETE /api/devices/{device_id}`

**Authentication**: Required

**CSRF**: Required

**Path Parameters**:
- `device_id` (int): Device ID

**Request**:
```bash
curl -X DELETE http://server:8000/api/devices/1 \
  -u admin:password \
  -H "X-CSRFToken: token-here"
```

**Response** (200 OK):
```json
{
  "message": "Device deleted successfully"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Device not found"
}
```

---

### Ports

#### List All Ports

Retrieve a list of all discovered ports across all devices.

**Endpoint**: `GET /api/ports`

**Authentication**: Required

**Request**:
```bash
curl -u admin:password http://server:8000/api/ports
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "device_id": 1,
    "port_num": 22,
    "protocol": "tcp",
    "name": "ssh",
    "product": "OpenSSH",
    "version": "8.2",
    "first_seen": "2024-01-01T10:00:00Z",
    "last_seen": "2024-01-04T15:30:00Z"
  },
  {
    "id": 2,
    "device_id": 1,
    "port_num": 80,
    "protocol": "tcp",
    "name": "http",
    "product": "nginx",
    "version": "1.18",
    "first_seen": "2024-01-01T10:00:00Z",
    "last_seen": "2024-01-04T15:30:00Z"
  }
]
```

---

#### Get Device Ports

Retrieve all ports for a specific device.

**Endpoint**: `GET /api/devices/{device_id}/ports`

**Authentication**: Required

**Path Parameters**:
- `device_id` (int): Device ID

**Request**:
```bash
curl -u admin:password http://server:8000/api/devices/1/ports
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "port_num": 22,
    "protocol": "tcp",
    "name": "ssh",
    "product": "OpenSSH",
    "version": "8.2"
  },
  {
    "id": 2,
    "port_num": 80,
    "protocol": "tcp",
    "name": "http",
    "product": "nginx",
    "version": "1.18"
  }
]
```

---

#### Add Port

Add a port to a device.

**Endpoint**: `POST /api/ports`

**Authentication**: Required

**CSRF**: Required

**Request Body**:
```json
{
  "device_id": 1,
  "port_num": 443,
  "protocol": "tcp",
  "name": "https",
  "product": "nginx",
  "version": "1.18"
}
```

**Required Fields**:
- `device_id` (int): Device ID
- `port_num` (int): Port number (1-65535)

**Optional Fields**:
- `protocol` (string): Protocol (tcp/udp)
- `name` (string): Service name
- `product` (string): Product name
- `version` (string): Version string

**Request**:
```bash
curl -X POST http://server:8000/api/ports \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "port_num": 443,
    "protocol": "tcp",
    "name": "https"
  }'
```

**Response** (201 Created):
```json
{
  "id": 3,
  "message": "Port created successfully"
}
```

---

#### Batch Add Ports

Add multiple ports to a device in a single request.

**Endpoint**: `POST /api/devices/{device_id}/ports/batch`

**Authentication**: Required

**CSRF**: Required

**Path Parameters**:
- `device_id` (int): Device ID

**Request Body**:
```json
[
  {
    "port_num": 80,
    "protocol": "tcp",
    "name": "http"
  },
  {
    "port_num": 443,
    "protocol": "tcp",
    "name": "https"
  }
]
```

**Request**:
```bash
curl -X POST http://server:8000/api/devices/1/ports/batch \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '[
    {"port_num": 80, "protocol": "tcp", "name": "http"},
    {"port_num": 443, "protocol": "tcp", "name": "https"}
  ]'
```

**Response** (200 OK):
```json
{
  "message": "Batch operation completed",
  "created": 2,
  "updated": 0,
  "errors": 0
}
```

---

#### Delete Port

Delete a port.

**Endpoint**: `DELETE /api/ports/{port_id}`

**Authentication**: Required

**CSRF**: Required

**Path Parameters**:
- `port_id` (int): Port ID

**Request**:
```bash
curl -X DELETE http://server:8000/api/ports/1 \
  -u admin:password \
  -H "X-CSRFToken: token-here"
```

**Response** (200 OK):
```json
{
  "message": "Port deleted successfully"
}
```

---

### Sensors

#### Register Sensor

Register a new sensor (gateway) or update existing.

**Endpoint**: `POST /api/sensors`

**Authentication**: Required

**CSRF**: Required

**Request Body**:
```json
{
  "mac": "00:11:22:33:44:aa",
  "hostname": "sensor1.local",
  "ip": "192.168.1.50"
}
```

**Required Fields**:
- `mac` (string): MAC address (unique identifier)

**Optional Fields**:
- `hostname` (string): Sensor hostname
- `ip` (string): Sensor IP address

**Request**:
```bash
curl -X POST http://server:8000/api/sensors \
  -u admin:password \
  -H "X-CSRFToken: token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:aa",
    "hostname": "sensor1.local",
    "ip": "192.168.1.50"
  }'
```

**Response** (201 Created):
```json
{
  "id": 1,
  "message": "Sensor registered successfully"
}
```

---

#### Update Sensor Heartbeat

Update sensor's last seen timestamp.

**Endpoint**: `POST /api/sensors/{sensor_id}/heartbeat`

**Authentication**: Required

**CSRF**: Required

**Path Parameters**:
- `sensor_id` (int): Sensor ID

**Request**:
```bash
curl -X POST http://server:8000/api/sensors/1/heartbeat \
  -u admin:password \
  -H "X-CSRFToken: token-here"
```

**Response** (200 OK):
```json
{
  "message": "Heartbeat updated successfully"
}
```

---

## Error Handling

### Error Response Structure

All errors return a JSON object with an `error` field:

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: CSRF token missing or invalid
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Common Error Messages

**Authentication Errors**:
```json
{"error": "Authentication required"}
{"error": "Invalid credentials"}
```

**Validation Errors**:
```json
{"error": "mac: Invalid MAC Address"}
{"error": "ip: Invalid IP Address"}
{"error": "hostname: Invalid Hostname"}
{"error": "port_num: Port number must be between 1 and 65535"}
```

**CSRF Errors**:
```json
{"error": "CSRF token missing or invalid"}
```

**Not Found Errors**:
```json
{"error": "Device not found"}
{"error": "Port not found"}
{"error": "Sensor not found"}
```

## Rate Limiting

Currently, the API does not implement rate limiting. For production deployments, it is recommended to implement rate limiting at the reverse proxy level (nginx, Apache, HAProxy).

**Recommended nginx configuration**:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://django_server;
}
```

## Client Examples

### Python Client

Complete Python client example with authentication and CSRF handling:

```python
import requests
from requests.auth import HTTPBasicAuth

class EasyNetVisibilityClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.csrf_token = None
    
    def get_csrf_token(self):
        """Get CSRF token for state-changing requests."""
        response = requests.get(
            f'{self.base_url}/api/csrf',
            auth=self.auth
        )
        response.raise_for_status()
        self.csrf_token = response.json()['csrfToken']
        return self.csrf_token
    
    def list_devices(self):
        """List all devices."""
        response = requests.get(
            f'{self.base_url}/api/devices',
            auth=self.auth
        )
        response.raise_for_status()
        return response.json()
    
    def add_device(self, mac, ip, hostname=None, vendor=None):
        """Add a new device."""
        if not self.csrf_token:
            self.get_csrf_token()
        
        data = {'mac': mac, 'ip': ip}
        if hostname:
            data['hostname'] = hostname
        if vendor:
            data['vendor'] = vendor
        
        response = requests.post(
            f'{self.base_url}/api/devices',
            json=data,
            headers={'X-CSRFToken': self.csrf_token},
            auth=self.auth
        )
        response.raise_for_status()
        return response.json()
    
    def batch_add_devices(self, devices):
        """Add multiple devices."""
        if not self.csrf_token:
            self.get_csrf_token()
        
        response = requests.post(
            f'{self.base_url}/api/devices/batch',
            json=devices,
            headers={'X-CSRFToken': self.csrf_token},
            auth=self.auth
        )
        response.raise_for_status()
        return response.json()

# Usage
client = EasyNetVisibilityClient(
    'http://server:8000',
    'admin',
    'password'
)

# List devices
devices = client.list_devices()
print(f"Found {len(devices)} devices")

# Add a device
result = client.add_device(
    mac='00:11:22:33:44:55',
    ip='192.168.1.100',
    hostname='newdevice.local'
)
print(f"Device added: {result}")
```

### Bash Script

```bash
#!/bin/bash

SERVER="http://localhost:8000"
USERNAME="admin"
PASSWORD="password"
AUTH="$USERNAME:$PASSWORD"

# Get CSRF token
CSRF_TOKEN=$(curl -s -u "$AUTH" "$SERVER/api/csrf" | jq -r '.csrfToken')

# List devices
echo "Listing devices:"
curl -s -u "$AUTH" "$SERVER/api/devices" | jq '.'

# Add a device
echo "Adding device:"
curl -s -X POST "$SERVER/api/devices" \
  -u "$AUTH" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:55",
    "ip": "192.168.1.100",
    "hostname": "newdevice.local"
  }' | jq '.'
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class EasyNetVisibilityClient {
  constructor(baseUrl, username, password) {
    this.baseUrl = baseUrl;
    this.auth = {
      username: username,
      password: password
    };
    this.csrfToken = null;
  }

  async getCsrfToken() {
    const response = await axios.get(
      `${this.baseUrl}/api/csrf`,
      { auth: this.auth }
    );
    this.csrfToken = response.data.csrfToken;
    return this.csrfToken;
  }

  async listDevices() {
    const response = await axios.get(
      `${this.baseUrl}/api/devices`,
      { auth: this.auth }
    );
    return response.data;
  }

  async addDevice(mac, ip, hostname = null, vendor = null) {
    if (!this.csrfToken) {
      await this.getCsrfToken();
    }

    const data = { mac, ip };
    if (hostname) data.hostname = hostname;
    if (vendor) data.vendor = vendor;

    const response = await axios.post(
      `${this.baseUrl}/api/devices`,
      data,
      {
        auth: this.auth,
        headers: { 'X-CSRFToken': this.csrfToken }
      }
    );
    return response.data;
  }
}

// Usage
(async () => {
  const client = new EasyNetVisibilityClient(
    'http://server:8000',
    'admin',
    'password'
  );

  // List devices
  const devices = await client.listDevices();
  console.log(`Found ${devices.length} devices`);

  // Add a device
  const result = await client.addDevice(
    '00:11:22:33:44:55',
    '192.168.1.100',
    'newdevice.local'
  );
  console.log('Device added:', result);
})();
```

---

For more information, see the [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md) documentation.
