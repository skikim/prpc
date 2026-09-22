from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0004_waitingoverride'),
    ]

    operations = [
        migrations.AlterField(
            model_name='holiday',
            name='holiday_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
