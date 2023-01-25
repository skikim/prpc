from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.CharField(max_length=10, null=True)
    phone_num = models.CharField(max_length=16, null=True)
    chart_num = models.CharField(max_length=10, null=True)


