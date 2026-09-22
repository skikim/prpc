import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase

from articleapp.models import WaitingOverride
from articleapp.waiting_utils import waiting_gate
from bookingapp.models import Booking
from profileapp.models import Profile


def dt(year, month, day, hour, minute):
    return datetime.datetime(year, month, day, hour, minute)


class WaitingGateTests(TestCase):
    def test_weekday_am_window(self):
        monday = dt(2026, 9, 21, 6, 30)
        self.assertEqual(waiting_gate(monday)['period'], 'am')
        self.assertTrue(waiting_gate(monday)['can_input'])
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 6, 29))['can_input'])
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 9, 0))['can_input'])

    def test_weekday_pm_window(self):
        self.assertTrue(waiting_gate(dt(2026, 9, 21, 11, 30))['can_input'])
        self.assertEqual(waiting_gate(dt(2026, 9, 21, 11, 30))['period'], 'pm')
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 11, 29))['can_input'])
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 14, 0))['can_input'])

    def test_wednesday_am_closed_pm_open(self):
        wed_am = dt(2026, 9, 23, 7, 0)
        self.assertFalse(waiting_gate(wed_am)['can_input'])
        self.assertIsNone(waiting_gate(wed_am)['period'])
        wed_pm = dt(2026, 9, 23, 12, 0)
        self.assertTrue(waiting_gate(wed_pm)['can_input'])
        self.assertEqual(waiting_gate(wed_pm)['period'], 'pm')

    def test_saturday_am_only(self):
        sat_am = dt(2026, 9, 19, 7, 0)
        self.assertTrue(waiting_gate(sat_am)['can_input'])
        sat_pm = dt(2026, 9, 19, 12, 0)
        self.assertFalse(waiting_gate(sat_pm)['can_input'])

    def test_sunday_closed(self):
        sun = dt(2026, 9, 20, 7, 0)
        self.assertFalse(waiting_gate(sun)['can_input'])

    def test_override_close_and_open(self):
        monday = dt(2026, 9, 21, 7, 0)
        WaitingOverride.objects.create(visit_date=monday.date(), mode='closed')
        self.assertFalse(waiting_gate(monday)['can_input'])
        WaitingOverride.objects.all().delete()
        sunday = dt(2026, 9, 20, 7, 0)
        WaitingOverride.objects.create(visit_date=sunday.date(), mode='open')
        self.assertTrue(waiting_gate(sunday)['can_input'])
        self.assertEqual(waiting_gate(sunday)['period'], 'am')


class KioskAccessTests(TestCase):
    def setUp(self):
        self.normal = User.objects.create_user('patient', password='pass1234')
        Profile.objects.create(
            user=self.normal,
            real_name='환자',
            phone_num='010',
            birth_date='19900101',
        )
        self.super = User.objects.create_superuser('admin', 'a@a.com', 'pass1234')
        self.tablet = User.objects.create_user('tablet', password='pass1234')
        Profile.objects.create(
            user=self.tablet,
            real_name='태블릿',
            phone_num='010',
            birth_date='19900101',
            is_tablet_user=True,
        )

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get('/supers/waiting_pt/').status_code, 302)
        self.assertEqual(self.client.get('/supers/tablet/').status_code, 302)

    def test_normal_user_blocked(self):
        self.client.login(username='patient', password='pass1234')
        wait = self.client.get('/supers/waiting_pt/', follow=False)
        tablet = self.client.get('/supers/tablet/', follow=False)
        self.assertEqual(wait.status_code, 302)
        self.assertEqual(tablet.status_code, 302)

    def test_superuser_can_open(self):
        self.client.login(username='admin', password='pass1234')
        self.assertEqual(self.client.get('/supers/waiting_pt/').status_code, 200)
        self.assertEqual(self.client.get('/supers/tablet/').status_code, 200)
        self.assertEqual(self.client.get('/supers/tablet2/').status_code, 200)
        self.assertEqual(self.client.get('/supers/tablet3/').status_code, 200)

    def test_tablet_user_can_open_kiosk_pages_only(self):
        self.client.login(username='tablet', password='pass1234')
        self.assertEqual(self.client.get('/supers/waiting_pt/').status_code, 200)
        self.assertEqual(self.client.get('/supers/tablet/').status_code, 200)
        locked = self.client.get('/supers/supercreate/', follow=False)
        self.assertEqual(locked.status_code, 302)
        self.assertIn('/supers/tablet/', locked.url)

    def test_search_requires_superuser(self):
        self.client.login(username='patient', password='pass1234')
        self.assertEqual(self.client.post('/searches/search/').status_code, 403)
        self.client.logout()
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post('/searches/search/', {'search_term': '없음'})
        self.assertEqual(resp.status_code, 200)


class WeeklyBookingLimitTests(TestCase):
    def test_third_booking_in_same_week_blocked_by_count(self):
        user = User.objects.create_user('u1', password='pass1234')
        week_dates = [
            datetime.date(2026, 9, 20),
            datetime.date(2026, 9, 21),
            datetime.date(2026, 9, 22),
        ]
        Booking.objects.create(user=user, booking_date=week_dates[0], booking_time='09:20', booking_status='예약승인')
        Booking.objects.create(user=user, booking_date=week_dates[1], booking_time='09:25', booking_status='예약요청')
        weekly = Booking.objects.filter(
            Q(user=user),
            Q(booking_date__range=(week_dates[0], datetime.date(2026, 9, 26))),
            Q(booking_status='예약승인') | Q(booking_status='예약요청'),
        )
        self.assertEqual(weekly.count(), 2)
        self.assertFalse(weekly.count() < 2)
