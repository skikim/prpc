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


class Holiday(models.Model):
    holiday_message = models.CharField(null=True, max_length=100)
