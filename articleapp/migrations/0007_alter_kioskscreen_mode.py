from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articleapp', '0006_kioskscreen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kioskscreen',
            name='mode',
            field=models.CharField(choices=[('wait', '대기 명단'), ('book', '14일'), ('book21', '21일'), ('book28', '28일')], default='wait', max_length=8),
        ),
    ]
