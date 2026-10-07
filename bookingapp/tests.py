import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from bookingapp.models import Booking
from profileapp.models import Profile


class SameDayBookingLimitTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user('patient', password='pass1234')
        Profile.objects.create(
            user=self.patient,
            real_name='홍길동',
            chart_num='8613',
            phone_num='01012345678',
            birth_date='900101',
        )
        self.day = datetime.date.today() + datetime.timedelta(days=1)
        self.client.login(username='patient', password='pass1234')

    def test_second_booking_on_the_same_day_is_rejected(self):
        Booking.objects.create(
            user=self.patient,
            booking_date=self.day,
            booking_time='09:20',
            booking_status='예약승인',
        )
        Booking.objects.create(booking_date=self.day, booking_time='14:20', booking_status='예약가능')

        response = self.client.post('/bookings/create/', {
            'date': self.day.isoformat(),
            'time': '14:20',
        })

        self.assertContains(response, '온라인 예약은 하루에 1회만 가능합니다.')
        self.assertTrue(Booking.objects.filter(
            booking_date=self.day,
            booking_time='14:20',
            booking_status='예약가능',
        ).exists())
        self.assertEqual(Booking.objects.filter(user=self.patient, booking_date=self.day).count(), 1)

    def test_chart_only_booking_blocks_the_same_patient(self):
        Booking.objects.create(
            booking_date=self.day,
            booking_time='09:20',
            booking_status='예약승인',
            booking_rn='홍길동8613',
        )

        response = self.client.post('/bookings/create2/', {
            'date': self.day.isoformat(),
            'time': '14:20',
        })

        self.assertContains(response, '온라인 예약은 하루에 1회만 가능합니다.')
        self.assertFalse(Booking.objects.filter(user=self.patient, booking_date=self.day).exists())

    @patch('bookingapp.views.send_discord_message_both')
    def test_another_day_is_still_allowed(self, _discord):
        other = self.day + datetime.timedelta(days=1)
        Booking.objects.create(
            user=self.patient,
            booking_date=self.day,
            booking_time='09:20',
            booking_status='예약승인',
        )
        Booking.objects.create(booking_date=other, booking_time='14:20', booking_status='예약가능')

        response = self.client.post('/bookings/create/', {
            'date': other.isoformat(),
            'time': '14:20',
        })

        self.assertEqual(response.status_code, 302)
        saved = Booking.objects.get(user=self.patient, booking_date=other, booking_time='14:20')
        self.assertEqual(saved.booking_status, '예약요청')
