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
- **gateway_timeout_minutes** (integer): Minutes before considering a gateway offline. Default: `10`

## Usage

### New Device Alerts

When a new device is detected on the network (added via the API), a Pushover notification will be sent automatically if `alert_new_device` is enabled. The notification includes:
- Device name (hostname or MAC if no hostname)
- IP address
- MAC address

### Gateway Timeout Monitoring

To monitor gateway timeouts and device offline status, you need to run the monitoring command periodically. This can be done using cron or a similar scheduler.

#### Running the Monitoring Command

```bash
# Navigate to the Django app directory
cd /opt/app/easy_net_visibility

# Run the monitoring command
python manage.py monitor_network
```

#### Setting up Automated Monitoring with Cron

Add a cron job to run the monitoring command every 5-10 minutes:

```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * cd /opt/app/easy_net_visibility && python manage.py monitor_network >> /var/log/network_monitor.log 2>&1
```

For Docker deployments, you can run the command inside the container:

```bash
# Add to crontab on the host
*/5 * * * * docker exec server python manage.py monitor_network >> /var/log/network_monitor.log 2>&1
```

Alternatively, you can add a supervisor configuration to run the monitoring as a periodic task.

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

1. Ensure the monitoring command is being run periodically (via cron or similar)
2. Check that `alert_gateway_timeout` is enabled
3. Verify that sensors have been offline for longer than `gateway_timeout_minutes`

### Device offline alerts not working

1. Ensure `alert_device_offline` is enabled
2. Verify the device has a nickname set (devices without nicknames won't trigger alerts)
3. Check that the device has been offline for more than 6 hours
4. Ensure the monitoring command is being run periodically

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
    "user_key": "uQiRzpo4DXghDmr9QzzfQu27cmVRsG",
    "api_token": "azGDORePK8gMaC0QOYAMyEEuzJnyUi",
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

The Pushover integration requires the `python-pushover` library, which is included in the `requirements.txt` file. It will be installed automatically when building the Docker image or when running `pip install -r requirements.txt`.
