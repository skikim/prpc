# Generated by Django 4.1.5 on 2023-01-29 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookingapp', '0002_rename_booked_on_time_booking_booked_on_datetime_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='booked_on_datetime',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
