import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from . import validators


# Create your models here.
class Device(models.Model):
    objects: models.Manager["Device"]  # type: ignore
    id = models.AutoField(primary_key=True, db_column='device_id')
    nickname = models.CharField(max_length=255, blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    ip = models.CharField(max_length=255)
    mac = models.CharField(max_length=255, db_index=True, unique=True)
    vendor = models.CharField(max_length=255, blank=True, null=True)
    first_seen = models.DateTimeField('first_seen')
    last_seen = models.DateTimeField('last_seen')
    last_notified_offline = models.DateTimeField('last_notified_offline', blank=True, null=True)

    def clean(self):
        """Validate device fields."""
        super().clean()
        errors = {}

        # Validate MAC address
        if not self.mac:
            errors['mac'] = 'Must Supply MAC Address'
        elif not validators.mac_address(self.mac):
            errors['mac'] = 'Invalid MAC Address'

        # Validate IP address (if provided and not empty)
        if self.ip and not validators.ip_address(self.ip):
            errors['ip'] = 'Invalid IP Address'

        # Validate hostname (if provided and not empty)
        if self.hostname and not validators.hostname(self.hostname):
            errors['hostname'] = 'Invalid Hostname'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs."""
        # Always call our custom clean() method which has validation logic
        self.clean()
        super().save(*args, **kwargs)

    def is_hidden(self):
        return self.nickname is None and not self.online()

    def name(self):
        if self.nickname is not None:
            return self.nickname
        else:
            return self.hostname

    def first_seen_today(self):
        return self.first_seen >= timezone.now() - datetime.timedelta(days=1)

    def online(self):
        return self.last_seen >= timezone.now() - datetime.timedelta(hours=6)

    def __str__(self):
        return str(self.name()) + "(" + self.ip + ")"

    class Meta:
        db_table = "devices"
        constraints = [
            models.UniqueConstraint(fields=['mac'], name='nk_device')
        ]


class Port(models.Model):
    objects: models.Manager["Port"]  # type: ignore
    id = models.AutoField(primary_key=True, db_column='port_id')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, db_index=True)
    port_num = models.IntegerField(db_index=True)
    protocol = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    product = models.CharField(max_length=255, blank=True, null=True)
    version = models.CharField(max_length=255, blank=True, null=True)
    first_seen = models.DateTimeField('first_seen')
    last_seen = models.DateTimeField('last_seen')

    def clean(self):
        """Validate port fields."""
        super().clean()
        errors = {}

        # Validate required fields
        if not self.device:
            errors['device'] = 'device not found'

        if self.port_num is None:
            errors['port_num'] = 'missing port number'

        if not self.protocol:
            errors['protocol'] = 'missing protocol'

        if not self.name:
            errors['name'] = 'missing port name'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs."""
        # Always call our custom clean() method which has validation logic
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.device) + " - " + str(self.name) + "(" + str(self.port_num) + ")"

    class Meta:
        db_table = "ports"
        constraints = [
            models.UniqueConstraint(fields=['device', 'port_num'], name='nk_port')
        ]
        unique_together = (('device', 'port_num'),)


class Sensor(models.Model):
    objects: models.Manager["Sensor"]  # type: ignore
    id = models.AutoField(primary_key=True, db_column='sensor_id')
    mac = models.CharField(max_length=255, db_index=True, unique=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    first_seen = models.DateTimeField('first_seen')
    last_seen = models.DateTimeField('last_seen')
    last_notified_timeout = models.DateTimeField('last_notified_timeout', blank=True, null=True)

    def clean(self):
        """Validate sensor fields."""
        super().clean()
        errors = {}

        # Validate MAC address (required)
        if not self.mac:
            errors['mac'] = 'Unknown Sensor MAC'

        # Note: hostname is optional (blank=True, null=True)
        # API-level validation may require it, but model allows None

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs."""
        # Always call our custom clean() method which has validation logic
        self.clean()
        super().save(*args, **kwargs)

    def time_since_last_seen(self):
        return int((timezone.now() - self.last_seen).total_seconds() / 60)

    def online(self):
        return self.last_seen >= timezone.now() - datetime.timedelta(minutes=5)

    def __str__(self):
        return str(self.hostname) + "(" + self.mac + ")"

    class Meta:
        db_table = "sensors"
        constraints = [
            models.UniqueConstraint(fields=['mac'], name='nk_sensor')
        ]
