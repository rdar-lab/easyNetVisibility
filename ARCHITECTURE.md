# Easy Net Visibility - Architecture Documentation

**Related Documentation**: [README.md](README.md) | [API.md](API.md) | [CONTRIBUTING.md](CONTRIBUTING.md) | [PUSHOVER.md](PUSHOVER.md)

---

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Models](#data-models)
- [Communication Flow](#communication-flow)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Scalability Considerations](#scalability-considerations)

## System Overview

Easy Net Visibility is a distributed network monitoring system consisting of:
- **Server**: Central Django application for data aggregation and visualization
- **Sensors**: Distributed scanning agents deployed across network segments
- **Database**: Persistent storage for device and port information
- **Notification Service**: Optional Pushover integration for real-time alerts

### Design Principles

1. **Distributed Architecture**: Multiple sensors can report to a single server
2. **Containerized Deployment**: All components run in Docker containers
3. **RESTful API**: Clean separation between sensors and server
4. **Flexible Database**: Support for SQLite, MySQL, or PostgreSQL
5. **Minimal Dependencies**: Core functionality requires only nmap and Python

## Component Architecture

### Server Component

```
┌─────────────────────────────────────────────────────────┐
│                   Django Server                         │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │              Web Interface Layer                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │  Admin   │  │Dashboard │  │   Static     │   │ │
│  │  │   UI     │  │   Views  │  │   Files      │   │ │
│  │  └──────────┘  └──────────┘  └──────────────┘   │ │
│  └───────────────────────────────────────────────────┘ │
│                         ▲                               │
│                         │                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │              REST API Layer                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │  Device  │  │   Port   │  │   Sensor     │   │ │
│  │  │   API    │  │   API    │  │    API       │   │ │
│  │  └──────────┘  └──────────┘  └──────────────┘   │ │
│  │  ┌──────────┐  ┌──────────┐                      │ │
│  │  │   CSRF   │  │   Auth   │                      │ │
│  │  │  Handler │  │  Handler │                      │ │
│  │  └──────────┘  └──────────┘                      │ │
│  └───────────────────────────────────────────────────┘ │
│                         ▲                               │
│                         │                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │              Business Logic Layer                  │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │  Device  │  │   Port   │  │   Sensor     │   │ │
│  │  │  Model   │  │  Model   │  │   Model      │   │ │
│  │  └──────────┘  └──────────┘  └──────────────┘   │ │
│  │  ┌──────────┐  ┌──────────┐                      │ │
│  │  │Validators│  │Monitoring│                      │ │
│  │  │          │  │ Service  │                      │ │
│  │  └──────────┘  └──────────┘                      │ │
│  └───────────────────────────────────────────────────┘ │
│                         ▲                               │
│                         │                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │              Data Access Layer                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │  Django  │  │Database  │  │   Query      │   │ │
│  │  │   ORM    │  │  Router  │  │Optimization  │   │ │
│  │  └──────────┘  └──────────┘  └──────────────┘   │ │
│  └───────────────────────────────────────────────────┘ │
│                         ▲                               │
│                         │                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │              External Services                     │ │
│  │  ┌──────────┐  ┌──────────┐                       │ │
│  │  │ Pushover │  │ Database │                       │ │
│  │  │ Notifier │  │ (SQLite/ │                       │ │
│  │  │          │  │MySQL/PG) │                       │ │
│  │  └──────────┘  └──────────┘                       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Key Server Components**:

1. **Web Interface Layer**:
   - Django Admin interface for management
   - Custom dashboard views
   - Static file serving (CSS, JS, images)

2. **REST API Layer**:
   - Device management endpoints
   - Port management endpoints
   - Sensor registration and heartbeat
   - CSRF token management
   - HTTP Basic Authentication

3. **Business Logic Layer**:
   - Django models with validation
   - Field validators (MAC, IP, hostname)
   - Background monitoring service
   - Pushover notification logic

4. **Data Access Layer**:
   - Django ORM for database abstraction
   - Support for multiple database backends
   - Database migrations

5. **External Services**:
   - Pushover API for notifications
   - Database (SQLite, MySQL, PostgreSQL)

### Sensor Component

```
┌─────────────────────────────────────────────────────┐
│                  Sensor Process                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           Main Control Loop                   │  │
│  │                                               │  │
│  │  while True:                                  │  │
│  │    1. Scan network (nmap)                    │  │
│  │    2. Query Fortigate (optional)             │  │
│  │    3. Normalize data                         │  │
│  │    4. Send to server                         │  │
│  │    5. Sleep / Wait                           │  │
│  └──────────────────────────────────────────────┘  │
│                      ▲                              │
│                      │                              │
│  ┌──────────────────────────────────────────────┐  │
│  │           Scanning Modules                    │  │
│  │  ┌──────────┐  ┌──────────┐                  │  │
│  │  │   Nmap   │  │Fortigate │                  │  │
│  │  │  Module  │  │  Module  │                  │  │
│  │  └──────────┘  └──────────┘                  │  │
│  └──────────────────────────────────────────────┘  │
│                      ▲                              │
│                      │                              │
│  ┌──────────────────────────────────────────────┐  │
│  │           Utility Modules                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ Network  │  │  Server  │  │  Config  │   │  │
│  │  │  Utils   │  │   API    │  │  Parser  │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘   │  │
│  │  ┌──────────┐  ┌──────────┐                 │  │
│  │  │  Logging │  │  Health  │                 │  │
│  │  │          │  │  Check   │                 │  │
│  │  └──────────┘  └──────────┘                 │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Key Sensor Components**:

1. **Main Control Loop** (`sensor.py`):
   - Orchestrates scanning and reporting
   - Handles configuration
   - Error recovery and logging
   - Continuous operation with sleep intervals

2. **Scanning Modules**:
   - **Nmap Module** (`nmap.py`):
     - Ping sweep for device discovery
     - Port scanning for service detection
     - XML output parsing
   - **Fortigate Module** (`fortigate.py`):
     - Assets API queries
     - ARP/DHCP fallback
     - Device normalization

3. **Utility Modules**:
   - **Network Utils** (`network_utils.py`):
     - Local IP/MAC detection
     - Interface management
     - Gateway detection
   - **Server API** (`server_api.py`):
     - REST API client
     - CSRF token management
     - Authentication
     - Batch operations
   - **Config Parser** (`config.py`):
     - INI file parsing
     - Configuration validation
   - **Logging** (`logs.py`):
     - Centralized logging
   - **Health Check** (`healthCheck.py`):
     - Sensor health monitoring

## Data Models

### Device Model

Represents a network device discovered by sensors.

```python
class Device:
    id: int                      # Primary key
    nickname: str | None         # User-assigned name
    hostname: str | None         # DNS hostname
    ip: str                      # IP address
    mac: str                     # MAC address (unique)
    vendor: str | None           # Vendor from MAC OUI
    first_seen: datetime         # First detection timestamp
    last_seen: datetime          # Last detection timestamp
    last_notified_offline: datetime | None  # Last offline notification
```

**Constraints**:
- `mac` must be unique
- `mac` format validated (XX:XX:XX:XX:XX:XX)
- `ip` format validated
- `hostname` format validated

**Methods**:
- `online()`: Returns true if seen in last 6 hours
- `first_seen_today()`: Returns true if first seen today
- `is_hidden()`: Returns true if no nickname and offline
- `name()`: Returns nickname or hostname

**Indexes**:
- Primary key on `id`
- Index on `mac` (unique)

### Port Model

Represents an open port on a device.

```python
class Port:
    id: int                      # Primary key
    device: Device               # Foreign key to Device
    port_num: int                # Port number (1-65535)
    protocol: str | None         # Protocol (tcp/udp)
    name: str | None             # Service name (http, ssh, etc.)
    product: str | None          # Product name (OpenSSH, nginx)
    version: str | None          # Version string
    first_seen: datetime         # First detection timestamp
    last_seen: datetime          # Last detection timestamp
```

**Constraints**:
- `port_num` required
- `device` foreign key with cascade delete

**Indexes**:
- Primary key on `id`
- Index on `device`
- Index on `port_num`

### Sensor Model

Represents a sensor (gateway) reporting to the server.

```python
class Sensor:
    id: int                      # Primary key
    mac: str                     # MAC address (unique)
    hostname: str | None         # Hostname
    ip: str | None               # IP address
    first_seen: datetime         # First registration
    last_seen: datetime          # Last heartbeat
    last_notified_offline: datetime | None  # Last offline notification
```

**Constraints**:
- `mac` must be unique
- `mac` format validated

**Methods**:
- `online()`: Returns true if seen in last 6 hours

**Indexes**:
- Primary key on `id`
- Index on `mac` (unique)

### Database Schema

```sql
-- Devices table
CREATE TABLE devices (
    device_id INTEGER PRIMARY KEY,
    nickname VARCHAR(255),
    hostname VARCHAR(255),
    ip VARCHAR(255),
    mac VARCHAR(255) UNIQUE NOT NULL,
    vendor VARCHAR(255),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    last_notified_offline TIMESTAMP
);

-- Ports table
CREATE TABLE ports (
    port_id INTEGER PRIMARY KEY,
    device_id INTEGER REFERENCES devices(device_id) ON DELETE CASCADE,
    port_num INTEGER,
    protocol VARCHAR(255),
    name VARCHAR(255),
    product VARCHAR(255),
    version VARCHAR(255),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP
);

-- Sensors table
CREATE TABLE sensors (
    sensor_id INTEGER PRIMARY KEY,
    mac VARCHAR(255) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    ip VARCHAR(255),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    last_notified_offline TIMESTAMP
);
```

## Communication Flow

### Device Discovery Flow

```
┌────────┐                ┌────────┐                ┌────────┐
│ Sensor │                │ Server │                │Database│
└───┬────┘                └───┬────┘                └───┬────┘
    │                         │                         │
    │ 1. Scan network         │                         │
    │─────────────────►       │                         │
    │    (nmap -sn)           │                         │
    │                         │                         │
    │ 2. Port scan devices    │                         │
    │─────────────────►       │                         │
    │    (nmap -p-)           │                         │
    │                         │                         │
    │ 3. Query Fortigate      │                         │
    │─────────────────►       │                         │
    │    (optional)           │                         │
    │                         │                         │
    │ 4. GET /api/csrf        │                         │
    │─────────────────────────►                         │
    │                         │                         │
    │ 5. CSRF Token           │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ 6. POST /api/devices/batch                        │
    │─────────────────────────►                         │
    │  [device1, device2...]  │                         │
    │                         │                         │
    │                         │ 7. Validate devices     │
    │                         │─────────────────────────►
    │                         │    Check MAC format     │
    │                         │    Check IP format      │
    │                         │    Check hostname       │
    │                         │                         │
    │                         │ 8. Upsert devices       │
    │                         │─────────────────────────►
    │                         │    INSERT or UPDATE     │
    │                         │    by MAC address       │
    │                         │                         │
    │                         │ 9. Send notification    │
    │                         │────────────────────────►│
    │                         │    (if new device)      │
    │                         │                         │
    │ 10. Success response    │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ 11. POST /api/devices/{id}/ports/batch            │
    │─────────────────────────►                         │
    │  [port1, port2...]      │                         │
    │                         │                         │
    │                         │ 12. Validate ports      │
    │                         │─────────────────────────►
    │                         │    Check port number    │
    │                         │                         │
    │                         │ 13. Upsert ports        │
    │                         │─────────────────────────►
    │                         │    INSERT or UPDATE     │
    │                         │                         │
    │ 14. Success response    │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ 15. Sleep (interval)    │                         │
    │                         │                         │
```

### Sensor Registration and Heartbeat

```
┌────────┐                ┌────────┐                ┌────────┐
│ Sensor │                │ Server │                │Database│
└───┬────┘                └───┬────┘                └───┬────┘
    │                         │                         │
    │ 1. POST /api/sensors    │                         │
    │─────────────────────────►                         │
    │  {mac, hostname, ip}    │                         │
    │                         │                         │
    │                         │ 2. Register sensor      │
    │                         │─────────────────────────►
    │                         │    INSERT or UPDATE     │
    │                         │    Set first_seen       │
    │                         │    Set last_seen        │
    │                         │                         │
    │ 3. Sensor ID            │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ ... scanning cycle ...  │                         │
    │                         │                         │
    │ 4. POST /api/sensors/{id}/heartbeat               │
    │─────────────────────────►                         │
    │                         │                         │
    │                         │ 5. Update last_seen     │
    │                         │─────────────────────────►
    │                         │                         │
    │ 6. Success              │                         │
    │◄─────────────────────────                         │
    │                         │                         │
```

### Monitoring and Notifications

```
┌────────┐                ┌────────┐                ┌────────┐
│Monitor │                │Database│                │Pushover│
│Service │                │        │                │        │
└───┬────┘                └───┬────┘                └───┬────┘
    │                         │                         │
    │ 1. Check sensors        │                         │
    │─────────────────────────►                         │
    │    SELECT WHERE         │                         │
    │    last_seen < now-10m  │                         │
    │                         │                         │
    │ 2. Offline sensors      │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ 3. Send notification    │                         │
    │─────────────────────────────────────────────────►│
    │    "Gateway timeout"    │                         │
    │                         │                         │
    │ 4. Update last_notified │                         │
    │─────────────────────────►                         │
    │                         │                         │
    │ 5. Check devices        │                         │
    │─────────────────────────►                         │
    │    SELECT WHERE         │                         │
    │    nickname IS NOT NULL │                         │
    │    AND last_seen < now-6h                         │
    │                         │                         │
    │ 6. Offline devices      │                         │
    │◄─────────────────────────                         │
    │                         │                         │
    │ 7. Send notification    │                         │
    │─────────────────────────────────────────────────►│
    │    "Device offline"     │                         │
    │                         │                         │
    │ 8. Update last_notified │                         │
    │─────────────────────────►                         │
    │                         │                         │
    │ 9. Sleep 5 minutes      │                         │
    │                         │                         │
```

## Deployment Architecture

### Single Server Deployment

```
┌───────────────────────────────────────────────┐
│              Network Segment                  │
│                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │Device│  │Device│  │Device│  │Device│     │
│  └──────┘  └──────┘  └──────┘  └──────┘     │
│      │         │         │         │         │
│      └─────────┼─────────┼─────────┘         │
│                │         │                   │
│         ┌──────▼─────────▼──────┐            │
│         │      Sensor           │            │
│         │   (Docker Host)       │            │
│         └──────────┬────────────┘            │
└────────────────────┼──────────────────────────┘
                     │
                     │ HTTPS
                     │
         ┌───────────▼──────────────┐
         │      Server Host         │
         │                          │
         │  ┌────────────────────┐  │
         │  │  Apache/Nginx      │  │
         │  │  (Reverse Proxy)   │  │
         │  └─────────┬──────────┘  │
         │            │              │
         │  ┌─────────▼──────────┐  │
         │  │  Django Server     │  │
         │  │  (Port 8000)       │  │
         │  └─────────┬──────────┘  │
         │            │              │
         │  ┌─────────▼──────────┐  │
         │  │  SQLite Database   │  │
         │  └────────────────────┘  │
         └──────────────────────────┘
```

### Multi-Sensor Deployment

```
┌─────────────────────────┐  ┌─────────────────────────┐
│    Network Segment A    │  │    Network Segment B    │
│                         │  │                         │
│  ┌──────┐  ┌──────┐    │  │  ┌──────┐  ┌──────┐    │
│  │Device│  │Device│    │  │  │Device│  │Device│    │
│  └──────┘  └──────┘    │  │  └──────┘  └──────┘    │
│      │         │        │  │      │         │        │
│      └─────────┘        │  │      └─────────┘        │
│            │            │  │            │            │
│      ┌─────▼─────┐      │  │      ┌─────▼─────┐      │
│      │ Sensor A  │      │  │      │ Sensor B  │      │
│      └─────┬─────┘      │  │      └─────┬─────┘      │
└────────────┼────────────┘  └────────────┼────────────┘
             │                            │
             │          Internet          │
             │              │             │
             └──────────────┼─────────────┘
                            │
                ┌───────────▼──────────────┐
                │     Central Server       │
                │                          │
                │  ┌────────────────────┐  │
                │  │  Reverse Proxy     │  │
                │  └─────────┬──────────┘  │
                │            │              │
                │  ┌─────────▼──────────┐  │
                │  │  Django Server     │  │
                │  └─────────┬──────────┘  │
                │            │              │
                │  ┌─────────▼──────────┐  │
                │  │  MySQL Database    │  │
                │  └────────────────────┘  │
                └──────────────────────────┘
```

### High-Availability Deployment

```
┌──────────────────────────────────────────────────────┐
│                 Load Balancer                        │
│                  (HAProxy)                           │
└─────────────┬────────────────────┬───────────────────┘
              │                    │
    ┌─────────▼─────────┐  ┌───────▼──────────┐
    │   Server Node 1   │  │   Server Node 2  │
    │                   │  │                  │
    │  ┌─────────────┐  │  │  ┌────────────┐  │
    │  │   Django    │  │  │  │   Django   │  │
    │  └──────┬──────┘  │  │  └─────┬──────┘  │
    └─────────┼─────────┘  └────────┼─────────┘
              │                     │
              └─────────┬───────────┘
                        │
              ┌─────────▼─────────┐
              │   MySQL Cluster   │
              │   (Master/Slave)  │
              └───────────────────┘
```

## Security Architecture

### Authentication and Authorization

1. **HTTP Basic Auth**:
   - All API endpoints require authentication
   - Username and password sent with each request
   - Server validates against Django user database

2. **CSRF Protection**:
   - POST/PUT/DELETE requests require CSRF token
   - Token obtained from `/api/csrf` endpoint
   - Token validated on each state-changing request

3. **Session Management**:
   - Django session framework
   - Session cookies for web interface
   - Configurable session timeout

### Network Security

1. **SSL/TLS**:
   - HTTPS recommended for production
   - Certificate validation in sensors
   - Self-signed certificates supported for testing

2. **Firewall Rules**:
   - Server: Restrict port 8000 (or 443 for HTTPS)
   - Sensor: Requires outbound HTTP/HTTPS only
   - Database: Restrict to local or trusted IPs

3. **API Security**:
   - Rate limiting (recommended via reverse proxy)
   - Input validation on all endpoints
   - SQL injection prevention (ORM)
   - XSS protection (Django templates)

### Data Security

1. **Secrets Management**:
   - SECRET_KEY for Django
   - Database credentials
   - API keys (Fortigate, Pushover)
   - Stored in configuration files (not in code)

2. **Data Validation**:
   - MAC address format validation
   - IP address format validation
   - Hostname format validation
   - Input sanitization

3. **Database Security**:
   - Encrypted connections (optional)
   - Strong password policies
   - Backup encryption (recommended)

## Scalability Considerations

### Vertical Scaling

**Server**:
- Increase CPU: Benefits Django request processing
- Increase RAM: Benefits database caching
- Increase storage: Benefits log retention and database growth
- Recommended: 2 CPU, 4GB RAM for 1000+ devices

**Database**:
- Use external database (MySQL/PostgreSQL) for better performance
- Enable query caching
- Optimize indexes on frequently queried fields

### Horizontal Scaling

**Multiple Sensors**:
- Deploy sensors in different network segments
- Each sensor operates independently
- All sensors report to same server
- No coordination required between sensors

**Multiple Servers** (future enhancement):
- Deploy load balancer (HAProxy, nginx)
- Use external database cluster
- Session storage in database or Redis
- Shared file storage for static files

### Performance Optimization

**Database**:
- Index on MAC address (already implemented)
- Index on last_seen for online() queries
- Periodic vacuum/optimize operations
- Archive old data (older than X months)

**API**:
- Batch operations for device/port updates
- Pagination for large result sets
- Caching frequently accessed data
- Async task queue for notifications (future)

**Sensors**:
- Adjust scan intervals based on network size
- Parallel nmap scanning (already implemented)
- Limit scan scope to relevant subnets
- Stagger sensor scan times to reduce server load

### Monitoring and Metrics

**Server Metrics**:
- Request rate and response time
- Database connection pool usage
- Memory and CPU utilization
- Error rate and types

**Sensor Metrics**:
- Scan duration and device count
- API success/failure rate
- Network interface status
- Memory and CPU utilization

**Business Metrics**:
- Total devices discovered
- New devices per day
- Device online/offline ratio
- Port changes over time
