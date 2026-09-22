from django.db import models

# Create your models here.

CHOICES = (
        (0, '0'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
)
class Waiting(models.Model):
    waiting_num = models.IntegerField(null=True, blank=True, choices=CHOICES)
    added_on_datetime = models.DateTimeField(auto_now=True)


class WaitingPatient(models.Model):
    PERIOD_CHOICES = (('am', '오전'), ('pm', '오후'))
    real_name = models.CharField(max_length=16)
    birth_date = models.CharField(max_length=8)
    visit_date = models.DateField()
    period = models.CharField(max_length=2, choices=PERIOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


class Holiday(models.Model):
    holiday_message = models.CharField(null=True, max_length=100)


class WaitingOverride(models.Model):
    MODE_CHOICES = (('open', '열기'), ('closed', '닫기'))
    visit_date = models.DateField(unique=True)
    mode = models.CharField(max_length=8, choices=MODE_CHOICES)
