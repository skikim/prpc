from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0003_waitingpatient'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaitingOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visit_date', models.DateField(unique=True)),
                ('mode', models.CharField(choices=[('open', '열기'), ('closed', '닫기')], max_length=8)),
            ],
        ),
    ]
