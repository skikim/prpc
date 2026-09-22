from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0002_holiday'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaitingPatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('real_name', models.CharField(max_length=16)),
                ('birth_date', models.CharField(max_length=8)),
                ('visit_date', models.DateField()),
                ('period', models.CharField(choices=[('am', '오전'), ('pm', '오후')], max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
