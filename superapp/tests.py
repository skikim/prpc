import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from bookingapp.models import Booking
from superapp.utils import other_weekly_booking_count, weekly_limit_cell_ids


class WeeklyLimitMarkTests(TestCase):
    def test_marks_only_the_second_booking(self):
        user = User.objects.create_user('p1', password='pass1234')
        other = User.objects.create_user('p2', password='pass1234')
        monday = datetime.date(2026, 9, 21)
        Booking.objects.create(user=user, booking_date=monday, booking_time='09:20', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=monday + datetime.timedelta(days=2), booking_time='14:20', booking_status='예약요청')
        Booking.objects.create(user=other, booking_date=monday, booking_time='09:25', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=monday + datetime.timedelta(days=8), booking_time='09:30', booking_status='예약승인')
        Booking.objects.create(booking_date=monday, booking_time='09:45', booking_status='예약승인')

        cells = weekly_limit_cell_ids([
            (1, monday),
            (2, monday + datetime.timedelta(days=1)),
            (3, monday + datetime.timedelta(days=2)),
        ])

        self.assertEqual(cells, ['r14:20c3'])

    def test_marks_visible_cell_when_the_other_booking_is_off_page(self):
        user = User.objects.create_user('p1', password='pass1234')
        monday = datetime.date(2026, 9, 21)
        Booking.objects.create(user=user, booking_date=monday, booking_time='10:05', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=monday - datetime.timedelta(days=1), booking_time='10:10', booking_status='예약요청')

        cells = weekly_limit_cell_ids([(1, monday)])

        self.assertEqual(cells, ['r10:05c1'])

    def test_drops_mark_when_the_first_booking_is_deleted(self):
        user = User.objects.create_user('p1', password='pass1234')
        monday = datetime.date(2026, 9, 21)
        friday = monday + datetime.timedelta(days=4)
        first = Booking.objects.create(user=user, booking_date=monday, booking_time='09:20', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=friday, booking_time='14:20', booking_status='예약승인')
        columns = [(1, friday)]

        self.assertEqual(weekly_limit_cell_ids(columns), ['r14:20c1'])
        first.delete()
        self.assertEqual(weekly_limit_cell_ids(columns), [])

    def test_third_notice_includes_past_and_ignores_deleted(self):
        user = User.objects.create_user('p1', password='pass1234')
        monday = datetime.date(2026, 9, 21)
        friday = monday + datetime.timedelta(days=4)
        wednesday = monday + datetime.timedelta(days=2)
        past = Booking.objects.create(user=user, booking_date=monday, booking_time='09:20', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=friday, booking_time='14:20', booking_status='예약승인')

        self.assertEqual(other_weekly_booking_count(user.id, wednesday, '10:05'), 2)
        past.delete()
        self.assertEqual(other_weekly_booking_count(user.id, wednesday, '10:05'), 1)
        self.assertEqual(other_weekly_booking_count(user.id, friday, '14:20'), 0)

    def test_weekly_third_notice_requires_superuser(self):
        staff = User.objects.create_superuser('admin', 'admin@example.com', 'pass1234')
        patient = User.objects.create_user('patient', password='pass1234')
        self.client.login(username='patient', password='pass1234')
        denied = self.client.get('/supers/weekly-third/', {'user_id': patient.id, 'date': '2026-09-23', 'time': '10:05'})
        self.assertEqual(denied.status_code, 403)
        self.client.login(username='admin', password='pass1234')
        allowed = self.client.get('/supers/weekly-third/', {'user_id': patient.id, 'date': '2026-09-23', 'time': '10:05'})
        self.assertEqual(allowed.status_code, 200)
        self.assertFalse(allowed.json()['warn'])
        staff.delete()
