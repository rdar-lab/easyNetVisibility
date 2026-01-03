from django.db import models
import datetime
from django.utils import timezone


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

    def __str__(self):
        return str(self.device) + " - " + str(self.name) + "(" + str(self.port_num) + ")"

    class Meta:
        db_table = "ports"
        constraints = [
            models.UniqueConstraint(fields=['device','port_num'], name='nk_port')
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
