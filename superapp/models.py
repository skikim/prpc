from django.db import models


class BackupSetting(models.Model):
    INTERVAL_CHOICES = (5, 10, 15)

    enabled = models.BooleanField(default=False)
    interval_minutes = models.PositiveSmallIntegerField(default=10)
    retention_days = models.PositiveSmallIntegerField(default=3)

    class Meta:
        verbose_name = '자동 백업'

    @classmethod
    def load(cls):
        setting, _created = cls.objects.get_or_create(pk=1)
        return setting
