# Generated by Django 4.1.5 on 2023-01-25 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profileapp', '0002_alter_profile_phone_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='phone_num',
            field=models.CharField(max_length=16, null=True),
        ),
    ]
