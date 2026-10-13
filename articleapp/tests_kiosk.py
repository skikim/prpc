import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase

from articleapp.models import KioskScreen, Waiting, WaitingBreak, WaitingOverride, WaitingPatient
from articleapp.waiting_utils import (
    homepage_waiting,
    is_legal_holiday,
    normalize_birth_date,
    notice_sessions,
    tablet_screen_off,
    waiting_gate,
    waiting_notice_visible,
)
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
        waiting = self.client.get('/supers/waiting_pt/')
        tablet = self.client.get('/supers/tablet/')
        self.assertEqual(waiting.status_code, 200)
        self.assertEqual(tablet.status_code, 200)
        self.assertContains(waiting, 'fully.turnScreenOff')
        self.assertContains(waiting, '20 * 60 + 30')
        self.assertContains(tablet, 'fully.turnScreenOff')
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

    def test_week_screens_open_booking_calendars(self):
        self.client.login(username='admin', password='pass1234')
        switched = self.client.post('/supers/waiting_list/', {'kiosk_mode': 'week1'})
        self.assertRedirects(switched, '/supers/waiting_list/')
        page = self.client.get('/supers/waiting_list/')
        self.assertContains(page, '현재: 1주차')
        self.assertContains(page, '2주차')
        self.client.logout()

        self.client.login(username='tablet', password='pass1234')
        booking = self.client.get('/supers/kiosk/')
        self.assertRedirects(booking, '/bookings/create/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/supers/kiosk/status/').json()['url'], '/bookings/create/')
        shown = self.client.get('/bookings/create/')
        self.assertEqual(shown.status_code, 200)
        self.assertContains(shown, 'kiosk/status')
        self.assertContains(shown, '예약 가능한 시간을 확인해 주세요.')
        blocked = self.client.post('/bookings/create/', {'date': '2026-10-12', 'time': '09:20'})
        self.assertRedirects(blocked, '/bookings/create/')
        self.assertFalse(Booking.objects.filter(user=self.tablet).exists())
        self.client.logout()

        self.client.login(username='admin', password='pass1234')
        self.client.post('/supers/waiting_list/', {'kiosk_mode': 'week2'})
        self.client.logout()
        self.client.login(username='tablet', password='pass1234')
        later = self.client.get('/supers/kiosk/')
        self.assertRedirects(later, '/bookings/create2/', fetch_redirect_response=False)
        shown = self.client.get('/bookings/create2/')
        self.assertEqual(shown.status_code, 200)
        self.assertContains(shown, 'kiosk/status')
        self.assertNotContains(shown, 'a.week-tab')
        blocked = self.client.post('/bookings/create2/', {'date': '2026-10-19', 'time': '09:20'})
        self.assertRedirects(blocked, '/bookings/create2/')
        self.client.logout()

        self.client.login(username='admin', password='pass1234')
        self.client.post('/supers/waiting_list/', {'kiosk_mode': 'week1'})
        self.client.logout()
        self.client.login(username='tablet', password='pass1234')
        switched_week = self.client.get('/bookings/create2/')
        self.assertEqual(switched_week.status_code, 200)
        self.assertEqual(KioskScreen.objects.get(pk=1).mode, 'week2')

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
        self.assertIn('screen_off', status.json())


class TabletScreenOffTests(TestCase):
    def test_sunday_stays_off_unless_opened(self):
        sunday = datetime.datetime(2026, 10, 11, 10, 0)
        self.assertTrue(tablet_screen_off(sunday))
        WaitingOverride.objects.create(visit_date=sunday.date(), mode='open')
        self.assertFalse(tablet_screen_off(sunday))

    def test_closed_switch_turns_the_screen_off_all_day(self):
        thursday = datetime.datetime(2026, 10, 8, 10, 0)
        self.assertFalse(tablet_screen_off(thursday))
        WaitingOverride.objects.create(visit_date=thursday.date(), mode='closed')
        self.assertTrue(tablet_screen_off(thursday))

    def test_legal_holiday_stays_off(self):
        self.assertTrue(tablet_screen_off(datetime.datetime(2026, 1, 1, 10, 0)))

    def test_wednesday_hours_stay_when_the_day_is_open(self):
        self.assertTrue(tablet_screen_off(datetime.datetime(2026, 10, 7, 9, 59)))
        self.assertFalse(tablet_screen_off(datetime.datetime(2026, 10, 7, 10, 0)))
        self.assertFalse(tablet_screen_off(datetime.datetime(2026, 10, 7, 15, 0)))
        self.assertTrue(tablet_screen_off(datetime.datetime(2026, 10, 7, 21, 0)))
        self.assertTrue(tablet_screen_off(datetime.datetime(2026, 10, 8, 4, 59)))
        self.assertFalse(tablet_screen_off(datetime.datetime(2026, 10, 8, 5, 0)))


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


class WaitingNoticeTests(TestCase):
    def test_saturday_afternoon_hidden(self):
        now = dt(2026, 10, 10, 12, 48)
        self.assertEqual(notice_sessions(now), {'am'})
        self.assertFalse(waiting_notice_visible(now, dt(2026, 10, 10, 12, 0)))

    def test_saturday_morning_shown(self):
        now = dt(2026, 10, 10, 7, 10)
        self.assertTrue(waiting_notice_visible(now, dt(2026, 10, 10, 6, 40)))

    def test_wednesday_morning_hidden_afternoon_shown(self):
        morning = dt(2026, 10, 7, 7, 30)
        self.assertEqual(notice_sessions(morning), {'pm'})
        self.assertFalse(waiting_notice_visible(morning, dt(2026, 10, 7, 7, 0)))
        afternoon = dt(2026, 10, 7, 12, 0)
        self.assertTrue(waiting_notice_visible(afternoon, dt(2026, 10, 7, 11, 40)))

    def test_sunday_and_holiday_hidden_unless_opened(self):
        sunday = dt(2026, 10, 11, 7, 30)
        self.assertFalse(waiting_notice_visible(sunday, dt(2026, 10, 11, 7, 0)))
        holiday = dt(2026, 9, 25, 7, 30)
        self.assertFalse(waiting_notice_visible(holiday, dt(2026, 9, 25, 7, 0)))
        WaitingOverride.objects.create(visit_date=sunday.date(), mode='open')
        self.assertTrue(waiting_notice_visible(sunday, dt(2026, 10, 11, 7, 0)))

    def test_closed_override_hides_weekday(self):
        thursday = dt(2026, 10, 8, 7, 30)
        self.assertTrue(waiting_notice_visible(thursday, dt(2026, 10, 8, 7, 0)))
        WaitingOverride.objects.create(visit_date=thursday.date(), mode='closed')
        self.assertFalse(waiting_notice_visible(thursday, dt(2026, 10, 8, 7, 0)))

    def test_homepage_hides_saturday_afternoon_card(self):
        Waiting.objects.create(id=1, waiting_num=2)
        Waiting.objects.filter(pk=1).update(added_on_datetime=dt(2026, 10, 10, 12, 0))
        with patch('articleapp.views.local_now', return_value=dt(2026, 10, 10, 12, 48)):
            page = self.client.get('/')
        self.assertContains(page, 'var allowAfternoon = false;')
        self.assertContains(page, "id='waiting_num_notice' class=\"alert-card waiting-card\" style=\"display: none;\"")

    def _patient(self, when, period, name):
        WaitingPatient.objects.create(
            real_name=name,
            birth_date='19900101',
            visit_date=when.date(),
            period=period,
        )

    def test_morning_count_switches_to_afternoon_tablet_count(self):
        morning = dt(2026, 10, 12, 7, 20)
        afternoon = dt(2026, 10, 12, 12, 30)
        self._patient(morning, 'am', '오전')
        self.assertEqual(homepage_waiting(morning, morning, 1)['number'], 1)
        self.assertEqual(homepage_waiting(morning, morning, 1)['period'], 'am')
        self.assertFalse(homepage_waiting(afternoon, morning, 1)['visible'])
        for name in ('오후1', '오후2', '오후3', '오후4'):
            self._patient(afternoon, 'pm', name)
        shown = homepage_waiting(afternoon, dt(2026, 10, 12, 12, 40), 0)
        self.assertTrue(shown['visible'])
        self.assertEqual(shown['period'], 'pm')
        self.assertEqual(shown['number'], 4)

    def test_homepage_shows_afternoon_tablet_count_over_manual_zero(self):
        Waiting.objects.create(id=1, waiting_num=0)
        Waiting.objects.filter(pk=1).update(added_on_datetime=dt(2026, 10, 12, 12, 10))
        afternoon = dt(2026, 10, 12, 12, 30)
        for name in ('오후1', '오후2', '오후3', '오후4'):
            self._patient(afternoon, 'pm', name)
        with patch('articleapp.views.local_now', return_value=afternoon):
            page = self.client.get('/')
        self.assertContains(page, 'class="waiting-number">4')
        self.assertContains(page, "var noticePeriod = 'pm';")
        self.assertNotContains(
            page,
            "id='waiting_num_notice' class=\"alert-card waiting-card\" style=\"display: none;\"",
        )
