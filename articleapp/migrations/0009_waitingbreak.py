from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0008_kioskscreen_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaitingBreak',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
    ]
