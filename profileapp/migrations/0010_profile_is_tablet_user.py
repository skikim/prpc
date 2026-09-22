from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profileapp', '0009_alter_profile_chart_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_tablet_user',
            field=models.BooleanField(default=False),
        ),
    ]
