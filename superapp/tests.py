import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from bookingapp.models import Booking
from superapp.utils import booking_rn_error, other_weekly_booking_count, other_weekly_chart_count, weekly_limit_cell_ids


class PastWeekPageTests(TestCase):
    def test_past_week_is_view_only(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pass1234')
        patient = User.objects.create_user('patient', password='pass1234')
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        booking = Booking.objects.create(
            booking_date=yesterday,
            booking_time='09:20',
            booking_status='예약승인',
            booking_rn='지난환자 9',
        )
        self.client.login(username='patient', password='pass1234')
        denied = self.client.get('/supers/supercreate_past/')
        self.assertEqual(denied.status_code, 302)
        self.client.login(username='admin', password='pass1234')
        page = self.client.get('/supers/supercreate_past/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '지난환자 9')
        self.assertNotContains(page, 'method="post"')
        self.client.post('/supers/supercreate_past/', {
            'date': yesterday.isoformat(),
            'time': '09:20',
            'status': '예약가능',
        })
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, '예약승인')


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
        Booking.objects.create(user=patient, booking_date=datetime.date(2026, 9, 21), booking_time='09:20', booking_status='예약승인')
        second = self.client.get('/supers/weekly-third/', {'user_id': patient.id, 'date': '2026-09-23', 'time': '10:05'})
        self.assertTrue(second.json()['warn'])
        self.assertEqual(second.json()['nth'], 2)
        self.assertEqual(second.json()['slots'], [{'date': '2026-09-21', 'time': '09:20'}])
        staff.delete()

    def test_chart_number_marks_only_the_second_booking(self):
        monday = datetime.date(2026, 9, 21)
        Booking.objects.create(booking_date=monday, booking_time='09:20', booking_status='예약승인', booking_rn='홍길동 8613')
        Booking.objects.create(booking_date=monday + datetime.timedelta(days=4), booking_time='14:20', booking_status='예약승인', booking_rn='홍길동8613')
        Booking.objects.create(booking_date=monday, booking_time='09:25', booking_status='예약승인', booking_rn='김철수 100')

        cells = weekly_limit_cell_ids([
            (1, monday),
            (5, monday + datetime.timedelta(days=4)),
        ])

        self.assertEqual(cells, ['r14:20c5'])

    def test_chart_notice_ignores_deleted_booking(self):
        monday = datetime.date(2026, 9, 21)
        friday = monday + datetime.timedelta(days=4)
        first = Booking.objects.create(booking_date=monday, booking_time='09:20', booking_status='예약승인', booking_rn='홍길동 8613')
        Booking.objects.create(booking_date=friday, booking_time='14:20', booking_status='예약승인', booking_rn='홍길동 8613')

        self.assertEqual(other_weekly_chart_count('8613', friday + datetime.timedelta(days=1), '10:05'), 2)
        first.delete()
        self.assertEqual(other_weekly_chart_count('8613', friday + datetime.timedelta(days=1), '10:05'), 1)


class BookingRnGuardTests(TestCase):
    def test_allows_name_chart_and_star(self):
        self.assertIsNone(booking_rn_error(None))
        self.assertIsNone(booking_rn_error(''))
        self.assertIsNone(booking_rn_error('*'))
        self.assertIsNone(booking_rn_error('권연이17888'))
        self.assertIsNone(booking_rn_error('홍길동 8613'))
        self.assertIsNone(booking_rn_error('Kim 12'))

    def test_rejects_symbols(self):
        message = '예약자명을 다시 확인한 뒤 저장하세요'
        self.assertEqual(booking_rn_error('권연이17888\\'), message)
        self.assertEqual(booking_rn_error('권연이17888₩'), message)
        self.assertEqual(booking_rn_error("홍길동'123"), message)
        self.assertEqual(booking_rn_error('김철수(초진)'), message)

    def test_invalid_name_is_not_saved_and_existing_booking_stays(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pass1234')
        self.client.login(username='admin', password='pass1234')
        day = datetime.date.today() + datetime.timedelta(days=8)
        existing = Booking.objects.create(
            booking_date=day,
            booking_time='12:30',
            booking_status='예약승인',
            booking_rn='기존환자1',
        )
        response = self.client.post('/supers/supercreate2/', {
            'date': day.isoformat(),
            'time': '12:30',
            'status': '예약승인',
            'booking_rn': '권연이17888\\',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '예약자명을 다시 확인한 뒤 저장하세요')
        existing.refresh_from_db()
        self.assertEqual(existing.booking_rn, '기존환자1')
        self.assertFalse(Booking.objects.filter(booking_rn__contains='\\').exists())

    def test_valid_name_is_saved(self):
        User.objects.create_superuser('admin2', 'admin2@example.com', 'pass1234')
        self.client.login(username='admin2', password='pass1234')
        day = datetime.date.today() + datetime.timedelta(days=8)
        response = self.client.post('/supers/supercreate2/', {
            'date': day.isoformat(),
            'time': '12:30',
            'status': '예약승인',
            'booking_rn': '권연이17888',
        })
        self.assertEqual(response.status_code, 302)
        saved = Booking.objects.get(booking_date=day, booking_time='12:30')
        self.assertEqual(saved.booking_rn, '권연이17888')
        self.assertEqual(saved.booking_status, '예약승인')

    def test_existing_backslash_does_not_break_page(self):
        User.objects.create_superuser('admin3', 'admin3@example.com', 'pass1234')
        self.client.login(username='admin3', password='pass1234')
        day = datetime.date.today() + datetime.timedelta(days=7)
        Booking.objects.create(
            booking_date=day,
            booking_time='12:30',
            booking_status='예약승인',
            booking_rn='권연이17888\\',
        )
        page = self.client.get('/supers/supercreate2/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '권연이17888\\u005C')
        self.assertNotContains(page, "17888\\'")
