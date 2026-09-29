from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0005_alter_holiday_holiday_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='KioskScreen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('wait', '대기 명단'), ('book', '예약')], default='wait', max_length=8)),
            ],
        ),
    ]
