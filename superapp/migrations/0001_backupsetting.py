from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='BackupSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False)),
                ('interval_minutes', models.PositiveSmallIntegerField(default=10)),
                ('retention_days', models.PositiveSmallIntegerField(default=3)),
            ],
            options={
                'verbose_name': '자동 백업',
            },
        ),
    ]
