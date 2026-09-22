from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookingapp', '0013_alter_booking_booking_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='booking_status',
            field=models.CharField(
                choices=[
                    ('예약가능', '예약가능'),
                    ('예약요청', '예약요청'),
                    ('예약승인', '예약승인'),
                    ('예약불가', '예약불가'),
                    ('선택중', '선택중'),
                ],
                max_length=10,
            ),
        ),
    ]
