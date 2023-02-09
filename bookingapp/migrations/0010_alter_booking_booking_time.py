# Generated by Django 4.1.5 on 2023-02-01 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookingapp', '0009_alter_booking_booking_time_alter_booking_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='booking_time',
            field=models.CharField(choices=[('09:20', '09:20'), ('09:25', '09:25'), ('09:30', '09:30'), ('09:45', '09:45'), ('09:50', '09:50'), ('09:55', '09:55'), ('10:05', '10:05'), ('10:10', '10:10'), ('10:15', '10:15'), ('10:30', '10:30'), ('10:35', '10:35'), ('10:40', '10:40'), ('10:50', '10:50'), ('10:55', '10:55'), ('11:00', '11:00'), ('11:15', '11:15'), ('11:20', '11:20'), ('11:25', '11:25'), ('11:35', '11:35'), ('11:40', '11:40'), ('11:45', '11:45'), ('12:00', '12:00'), ('12:05', '12:05'), ('12:10', '12:10'), ('12:20', '12:20'), ('12:25', '12:25'), ('12:30', '12:30'), ('13:00', '점심시간'), ('14:20', '14:20'), ('14:25', '14:25'), ('14:30', '14:30'), ('14:45', '14:45'), ('14:50', '14:50'), ('14:55', '14:55'), ('15:05', '15:05'), ('15:10', '15:10'), ('15:15', '15:15'), ('15:30', '15:30'), ('15:35', '15:35'), ('15:40', '15:40'), ('15:50', '15:50'), ('15:55', '15:55'), ('16:00', '16:00'), ('16:15', '16:15'), ('16:20', '16:20'), ('16:25', '16:25'), ('16:35', '16:35'), ('16:40', '16:40'), ('16:45', '16:45'), ('17:00', '17:00'), ('17:05', '17:05'), ('17:10', '17:10'), ('17:20', '17:20'), ('17:25', '17:25'), ('17:30', '17:30'), ('17:45', '17:45'), ('17:50', '17:50'), ('17:55', '17:55'), ('18:05', '18:05'), ('18:10', '18:10'), ('18:15', '18:15'), ('18:30', '18:30'), ('18:35', '18:35'), ('18:40', '18:40'), ('18:50', '18:50'), ('18:55', '18:55'), ('19:00', '19:00'), ('19:15', '19:15'), ('19:20', '19:20'), ('19:25', '19:25'), ('19:35', '19:35'), ('19:40', '19:40'), ('19:45', '19:45'), ('20:00', '20:00'), ('20:05', '20:05')], max_length=16),
        ),
    ]
