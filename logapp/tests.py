import datetime
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from bookingapp.models import Booking
from logapp.cleanup import (
    CLEANUP_COOLDOWN_KEY,
    CLEANUP_DONE_DATE_KEY,
    CLEANUP_LOCK_KEY,
    cleanup_old_booking_logs,
    maybe_cleanup_old_booking_logs,
)
from logapp.models import BookingLog


class BookingLogAutoCleanupTests(TestCase):
    def setUp(self):
        cache.delete_many([CLEANUP_DONE_DATE_KEY, CLEANUP_COOLDOWN_KEY, CLEANUP_LOCK_KEY])
        self.admin = User.objects.create_superuser('log-admin', 'log@example.com', 'pass1234')

    def _make_log(self, days_ago, booking_time='09:20'):
        target_dt = datetime.datetime.now() - timedelta(days=days_ago)
        log = BookingLog.objects.create(
            action_type='CREATE',
            booking_date=target_dt.date(),
            booking_time=booking_time,
            new_status='예약요청',
            notes=f'{days_ago}일 전 로그',
        )
        BookingLog.objects.filter(pk=log.pk).update(created_at=target_dt)
        return log

    def test_cleanup_removes_only_logs_older_than_90_days(self):
        old_91 = self._make_log(91)
        old_120 = self._make_log(120)
        keep_89 = self._make_log(89)
        keep_0 = self._make_log(0)

        deleted, has_more = cleanup_old_booking_logs(days=90)

        self.assertEqual(deleted, 2)
        self.assertFalse(has_more)
        self.assertFalse(BookingLog.objects.filter(pk__in=[old_91.pk, old_120.pk]).exists())
        self.assertTrue(BookingLog.objects.filter(pk=keep_89.pk).exists())
        self.assertTrue(BookingLog.objects.filter(pk=keep_0.pk).exists())

    def test_maybe_cleanup_runs_once_per_day_when_caught_up(self):
        self._make_log(100)
        first = maybe_cleanup_old_booking_logs(days=90)
        self.assertEqual(first, 1)

        # Same day: daily cache guard skips redundant cleanup
        late = self._make_log(100)
        second = maybe_cleanup_old_booking_logs(days=90)
        self.assertEqual(second, 0)
        self.assertTrue(BookingLog.objects.filter(pk=late.pk).exists())

    def test_backlog_drains_in_bounded_batches_without_setting_daily_done(self):
        for i in range(5):
            self._make_log(100 + i)

        first = maybe_cleanup_old_booking_logs(days=90, batch_size=2, max_batches=1)
        self.assertEqual(first, 2)
        self.assertIsNone(cache.get(CLEANUP_DONE_DATE_KEY))
        self.assertEqual(BookingLog.objects.count(), 3)

        # After cooldown clears, next run finishes the backlog and marks today done
        cache.delete(CLEANUP_COOLDOWN_KEY)
        second = maybe_cleanup_old_booking_logs(days=90, batch_size=2, max_batches=5)
        self.assertEqual(second, 3)
        self.assertEqual(cache.get(CLEANUP_DONE_DATE_KEY), datetime.date.today().isoformat())
        self.assertEqual(BookingLog.objects.count(), 0)

    def test_visiting_log_list_triggers_auto_cleanup(self):
        old_log = self._make_log(95)
        recent_log = self._make_log(3)

        self.client.login(username='log-admin', password='pass1234')
        resp = self.client.get('/log/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '90일 이전 로그는 자동으로 정리됩니다.')
        self.assertFalse(BookingLog.objects.filter(pk=old_log.pk).exists())
        self.assertTrue(BookingLog.objects.filter(pk=recent_log.pk).exists())

    def test_booking_signal_triggers_auto_cleanup(self):
        old_log = self._make_log(100)
        Booking.objects.create(
            booking_date=datetime.date.today() + datetime.timedelta(days=1),
            booking_time='09:20',
            booking_status='예약가능',
        )
        self.assertFalse(BookingLog.objects.filter(pk=old_log.pk).exists())
