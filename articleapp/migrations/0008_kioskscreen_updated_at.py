import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0007_alter_kioskscreen_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='kioskscreen',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime.now),
            preserve_default=False,
        ),
    ]
