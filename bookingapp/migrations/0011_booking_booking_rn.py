# Generated by Django 4.1.5 on 2023-03-20 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookingapp', '0010_alter_booking_booking_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='booking_rn',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
