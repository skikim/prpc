from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    real_name = models.CharField(max_length=16, null=True)
    birth_date = models.CharField(max_length=10, null=True)
    phone_num = models.CharField(max_length=16, null=True)
    chart_num = models.CharField(max_length=10, null=True, unique=True)

    def __str__(self):
        return self.real_name


