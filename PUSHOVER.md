# Pushover Integration

EasyNetVisibility supports Pushover integration for real-time notifications about network events.

## Features

The Pushover integration provides three types of alerts:

1. **New Device Detection** - Alert when a new device is detected on the network
2. **Gateway Timeout** - Alert when a gateway (sensor) hasn't reported in for a configurable timeout period
3. **Device Offline** - Alert when a device goes offline (disabled by default)

Each alert type can be individually enabled or disabled through configuration.

## Prerequisites

1. A Pushover account - Sign up at https://pushover.net/
2. Create an application in Pushover to get an API token
3. Get your User Key from your Pushover dashboard

## Configuration

Add the following configuration to your `conf/settings.json` file:

```json
{
  "PUSHOVER_CONFIG": {
    "enabled": true,
    "user_key": "YOUR_PUSHOVER_USER_KEY",
    "api_token": "YOUR_PUSHOVER_API_TOKEN",
    "alert_new_device": true,
    "alert_gateway_timeout": true,
    "alert_device_offline": false,
    "gateway_timeout_minutes": 10
  }
}
```

### Configuration Options

- **enabled** (boolean): Master switch to enable/disable all Pushover notifications. Default: `false`
- **user_key** (string): Your Pushover user key (required if enabled)
- **api_token** (string): Your Pushover application API token (required if enabled)
- **alert_new_device** (boolean): Enable notifications for new devices detected on the network. Default: `false`
- **alert_gateway_timeout** (boolean): Enable notifications when gateways (sensors) go offline. Default: `false`
- **alert_device_offline** (boolean): Enable notifications when devices go offline. Default: `false`
  - Note: Only devices with a nickname (marked as important) will trigger offline alerts
- **gateway_timeout_minutes** (integer): Minutes before considering a gateway offline. Valid range: 1–1440. Values outside this range are ignored and the default of 10 minutes is used with a warning. Default: `10`

## Usage

### New Device Alerts

When a new device is detected on the network (added via the API), a Pushover notification will be sent automatically if `alert_new_device` is enabled. The notification includes:
- Device name (hostname or MAC if no hostname)
- IP address
- MAC address

### Gateway Timeout and Device Offline Monitoring

The monitoring service runs automatically as a background thread when the Django server starts. It checks for gateway timeouts and device offline events every 5 minutes by default.

**No additional setup is required** - monitoring starts automatically with the server.

#### How It Works

- The monitoring service starts automatically when Django initializes
- Runs as a daemon thread in the background
- Checks every 5 minutes for:
  - Gateways (sensors) that haven't reported in
  - Devices with nicknames that have gone offline
- Survives across container restarts using database-persisted state
- Works in both standalone and Kubernetes deployments

#### Manual Monitoring (Optional)

If you need to trigger a manual check or prefer to run monitoring separately, you can use the management command:

```bash
# Navigate to the Django app directory (adjust path to your installation)
cd /path/to/easyNetVisibility/server/server_django/easy_net_visibility

# Run the monitoring command manually
python manage.py monitor_network
```

This is useful for:
- Testing notifications
- Running monitoring independently
- Troubleshooting issues

### Device Offline Alerts

Device offline alerts are only sent for devices that have a **nickname** set. This ensures that only devices you care about (that you've explicitly named) trigger offline notifications.

The system checks if a device hasn't been seen in the last 6 hours (matching the `online()` method in the Device model).

## Notification Priority Levels

- **New Device**: Priority 0 (normal)
- **Gateway Timeout**: Priority 1 (high - bypasses quiet hours)
- **Device Offline**: Priority 0 (normal)

## Testing the Integration

To test your Pushover configuration:

1. Enable Pushover in your `conf/settings.json`
2. Set `alert_new_device` to `true`
3. Restart the Django server
4. Add a test device through the API or wait for the sensor to detect a new device
5. You should receive a Pushover notification

For testing gateway timeout alerts:

```bash
# Run the monitoring command manually
python manage.py monitor_network
```

Check the logs for any errors related to Pushover notifications.

## Troubleshooting

### No notifications are being sent

1. Verify `enabled` is set to `true` in the configuration
2. Check that your `user_key` and `api_token` are correct
3. Ensure the specific alert type (e.g., `alert_new_device`) is enabled
4. Check the Django logs for error messages related to Pushover

### Gateway timeout alerts not working

1. Check that `alert_gateway_timeout` is enabled
2. Verify that sensors have been offline for longer than `gateway_timeout_minutes`
3. Check the Django logs for error messages related to Pushover
4. The monitoring service runs automatically with the Django server

### Device offline alerts not working

1. Ensure `alert_device_offline` is enabled
2. Verify the device has a nickname set (devices without nicknames won't trigger alerts)
3. Check that the device has been offline for more than 6 hours
4. The monitoring service runs automatically with the Django server

## Example Full Configuration

```json
{
  "DATABASES": {
    "default": {
      "ENGINE": "django.db.backends.sqlite3",
      "NAME": "db/db.sqlite3"
    }
  },
  "SECRET_KEY": "your-secret-key-here",
  "DEBUG": "False",
  "STATIC_ROOT": "static",
  "PUSHOVER_CONFIG": {
    "enabled": true,
    "user_key": "uXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "api_token": "aXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "alert_new_device": true,
    "alert_gateway_timeout": true,
    "alert_device_offline": false,
    "gateway_timeout_minutes": 15
  }
}
```

## Security Notes

- Keep your `user_key` and `api_token` secure
- Do not commit these values to version control
- Use environment-specific configuration files
- Consider using environment variables for sensitive values

## Dependencies

The Pushover integration requires the `pushover-complete` library, which is included in the `requirements.txt` file. It will be installed automatically when building the Docker image or when running `pip install -r requirements.txt`.
