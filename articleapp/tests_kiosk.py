import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase

from articleapp.models import KioskScreen, WaitingBreak, WaitingOverride
from articleapp.waiting_utils import is_legal_holiday, normalize_birth_date, waiting_gate
from superapp.views import kiosk_screen_mode
from bookingapp.models import Booking
from profileapp.models import Profile


def dt(year, month, day, hour, minute):
    return datetime.datetime(year, month, day, hour, minute)


class WaitingGateTests(TestCase):
    def test_weekday_am_window(self):
        monday = dt(2026, 9, 21, 6, 30)
        self.assertEqual(waiting_gate(monday)['period'], 'am')
        self.assertTrue(waiting_gate(monday)['can_input'])
        early = waiting_gate(dt(2026, 9, 21, 6, 29))
        self.assertFalse(early['can_input'])
        self.assertIn('자동으로', early['message'])
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 9, 0))['can_input'])

    def test_weekday_pm_window(self):
        self.assertTrue(waiting_gate(dt(2026, 9, 21, 11, 30))['can_input'])
        self.assertEqual(waiting_gate(dt(2026, 9, 21, 11, 30))['period'], 'pm')
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 11, 29))['can_input'])
        self.assertFalse(waiting_gate(dt(2026, 9, 21, 14, 0))['can_input'])

    def test_wednesday_am_closed_pm_open(self):
        wed_am = dt(2026, 9, 23, 7, 0)
        self.assertFalse(waiting_gate(wed_am)['can_input'])
        self.assertIn('11시 30분', waiting_gate(wed_am)['message'])
        self.assertIn('자동으로', waiting_gate(wed_am)['message'])
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

    def test_legal_holiday_closed_unless_opened(self):
        chuseok = dt(2026, 9, 25, 7, 0)
        self.assertFalse(waiting_gate(chuseok)['can_input'])
        self.assertIn('공휴일', waiting_gate(chuseok)['message'])
        WaitingOverride.objects.create(visit_date=chuseok.date(), mode='open')
        opened = waiting_gate(chuseok)
        self.assertTrue(opened['can_input'])
        self.assertEqual(opened['period'], 'am')
        substitute = waiting_gate(dt(2026, 3, 2, 12, 0))
        self.assertFalse(substitute['can_input'])
        self.assertIn('공휴일', substitute['message'])
        election = waiting_gate(dt(2026, 6, 3, 12, 0))
        self.assertFalse(election['can_input'])
        self.assertIn('공휴일', election['message'])
        self.assertTrue(is_legal_holiday(datetime.date(2026, 6, 3)))


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

    def test_kiosk_follows_superuser_screen(self):
        self.client.login(username='tablet', password='pass1234')
        waiting = self.client.get('/supers/kiosk/')
        self.assertRedirects(waiting, '/supers/waiting_pt/', fetch_redirect_response=False)
        status = self.client.get('/supers/kiosk/status/')
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()['mode'], 'wait')
        self.client.logout()

        self.client.login(username='admin', password='pass1234')
        switched = self.client.post('/supers/waiting_list/', {'kiosk_mode': 'book'})
        self.assertRedirects(switched, '/supers/waiting_list/')
        page = self.client.get('/supers/waiting_list/')
        self.assertContains(page, '태블릿 화면')
        self.assertContains(page, '현재: 14일')
        later = self.client.post('/supers/waiting_list/', {'kiosk_mode': 'book21'})
        self.assertRedirects(later, '/supers/waiting_list/')
        self.client.logout()

        self.client.login(username='tablet', password='pass1234')
        booking = self.client.get('/supers/kiosk/')
        self.assertRedirects(booking, '/supers/tablet2/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/supers/kiosk/status/').json()['url'], '/supers/tablet2/')
        self.client.logout()
        self.client.login(username='admin', password='pass1234')
        self.client.post('/supers/waiting_list/', {'kiosk_mode': 'book'})
        self.client.logout()
        self.client.login(username='tablet', password='pass1234')
        booking = self.client.get('/supers/kiosk/')
        self.assertRedirects(booking, '/supers/tablet/', fetch_redirect_response=False)
        blocked = self.client.post('/supers/waiting_list/', {'kiosk_mode': 'wait'})
        self.assertEqual(blocked.status_code, 302)
        self.assertIn('/supers/tablet/', blocked.url)
        self.assertEqual(self.client.get('/supers/kiosk/status/').json()['mode'], 'book')

    def test_kiosk_blocks_normal_user(self):
        self.client.login(username='patient', password='pass1234')
        resp = self.client.get('/supers/kiosk/', follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn('/supers/waiting_pt/', resp.url)
        self.assertEqual(self.client.get('/supers/kiosk/status/').status_code, 403)

    def test_waiting_switch_sets_day_exception(self):
        self.client.login(username='admin', password='pass1234')
        today = datetime.date.today()
        closed_by_default = today.weekday() == 6 or is_legal_holiday(today)
        page = self.client.get('/supers/waiting_list/')
        self.assertContains(page, '진료함' if closed_by_default else '쉽니다')
        self.assertNotContains(page, '오늘 열기')
        self.client.post('/supers/waiting_list/', {'override_day': 'today', 'override_switch': 'on'})
        saved = WaitingOverride.objects.get(visit_date=today)
        self.assertEqual(saved.mode, 'open' if closed_by_default else 'closed')
        self.client.post('/supers/waiting_list/', {'override_day': 'today', 'override_switch': 'off'})
        self.assertFalse(WaitingOverride.objects.filter(visit_date=today).exists())

    def test_waiting_break_closes_range_and_cancel_clears_it(self):
        self.client.login(username='admin', password='pass1234')
        start = datetime.date.today() + datetime.timedelta(days=2)
        end = start + datetime.timedelta(days=2)
        saved = self.client.post('/supers/waiting_list/', {
            'break_action': 'save',
            'break_start': start.isoformat(),
            'break_end': end.isoformat(),
        })
        self.assertRedirects(saved, '/supers/waiting_list/')
        self.assertEqual(WaitingOverride.objects.filter(visit_date__range=(start, end), mode='closed').count(), 3)
        closed = waiting_gate(datetime.datetime.combine(start, datetime.time(7, 0)))
        self.assertFalse(closed['can_input'])
        page = self.client.get('/supers/waiting_list/')
        self.assertContains(page, '까지 쉽니다')
        self.client.post('/supers/waiting_list/', {'break_action': 'clear'})
        self.assertFalse(WaitingBreak.objects.exists())
        self.assertFalse(WaitingOverride.objects.filter(visit_date__range=(start, end)).exists())

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


class KioskDailyResetTests(TestCase):
    def set_changed_at(self, when, mode='book'):
        screen, _ = KioskScreen.objects.update_or_create(pk=1, defaults={'mode': mode})
        KioskScreen.objects.filter(pk=screen.pk).update(updated_at=when)
        return screen

    def test_before_18_keeps_manual_screen(self):
        self.set_changed_at(datetime.datetime(2026, 9, 30, 17, 0))
        self.assertEqual(kiosk_screen_mode(datetime.datetime(2026, 9, 30, 17, 59)), 'book')

    def test_at_18_resets_to_wait(self):
        self.set_changed_at(datetime.datetime(2026, 9, 30, 17, 0))
        self.assertEqual(kiosk_screen_mode(datetime.datetime(2026, 9, 30, 18, 0)), 'wait')
        self.assertEqual(KioskScreen.objects.get(pk=1).mode, 'wait')

    def test_manual_change_after_18_sticks_until_next_day(self):
        self.set_changed_at(datetime.datetime(2026, 9, 30, 18, 10))
        self.assertEqual(kiosk_screen_mode(datetime.datetime(2026, 9, 30, 19, 0)), 'book')
        self.assertEqual(kiosk_screen_mode(datetime.datetime(2026, 10, 1, 7, 0)), 'wait')

    def test_status_poll_applies_missed_reset(self):
        tablet = User.objects.create_user('tablet-reset', password='pass1234')
        Profile.objects.create(
            user=tablet,
            real_name='태블릿',
            phone_num='010',
            birth_date='19900101',
            is_tablet_user=True,
        )
        self.client.login(username='tablet-reset', password='pass1234')
        self.set_changed_at(datetime.datetime(2000, 1, 1, 10, 0), mode='book21')
        status = self.client.get('/supers/kiosk/status/')
        self.assertEqual(status.json()['mode'], 'wait')
        self.assertEqual(status.json()['url'], '/supers/waiting_pt/')


class NormalizeBirthDateTests(TestCase):
    today = datetime.date(2026, 9, 30)

    def test_eight_digits_kept(self):
        self.assertEqual(normalize_birth_date('19620428', self.today), '19620428')

    def test_six_digits_expand_to_1900s(self):
        self.assertEqual(normalize_birth_date('620428', self.today), '19620428')

    def test_six_digits_expand_to_2000s(self):
        self.assertEqual(normalize_birth_date('100101', self.today), '20100101')

    def test_invalid_rejected(self):
        self.assertIsNone(normalize_birth_date('620431', self.today))
        self.assertIsNone(normalize_birth_date('19000101', self.today))
        self.assertIsNone(normalize_birth_date('12345', self.today))
