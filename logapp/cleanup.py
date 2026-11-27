"""
예약 로그 90일(3개월) 자동 정리 유틸리티
별도 서버 cron 설정 없이 하루 1회 자동으로 90일 이전 로그를 배치 삭제합니다.
"""
import datetime
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from logapp.models import BookingLog

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_DAYS = 90
CLEANUP_DONE_DATE_KEY = 'booking_log_cleanup_done_date'
CLEANUP_COOLDOWN_KEY = 'booking_log_cleanup_cooldown'
CLEANUP_LOCK_KEY = 'booking_log_cleanup_lock'


def get_retention_days(days=None):
    if days is not None:
        return int(days)
    return int(getattr(settings, 'BOOKING_LOG_RETENTION_DAYS', DEFAULT_RETENTION_DAYS))


def retention_cutoff(days=None, today=None):
    retention = get_retention_days(days)
    base_date = today or date.today()
    cutoff_date = base_date - timedelta(days=retention)
    return datetime.datetime.combine(cutoff_date, datetime.time.min)


def cleanup_old_booking_logs(days=None, batch_size=1000, max_batches=None, today=None):
    """
    보관 기간(기본 90일)이 지난 BookingLog를 배치 단위로 삭제합니다.
    Returns:
        tuple[int, bool]: (삭제된 총 건수, 남은 삭제 대상 존재 여부)
    """
    cutoff_dt = retention_cutoff(days=days, today=today)
    deleted_total = 0
    batches = 0

    while True:
        if max_batches is not None and batches >= max_batches:
            has_more = BookingLog.objects.filter(created_at__lt=cutoff_dt).exists()
            return deleted_total, has_more

        batch_ids = list(
            BookingLog.objects.filter(created_at__lt=cutoff_dt)
            .order_by('id')
            .values_list('id', flat=True)[:batch_size]
        )
        if not batch_ids:
            return deleted_total, False

        with transaction.atomic():
            deleted_count, _ = BookingLog.objects.filter(id__in=batch_ids).delete()

        deleted_total += deleted_count
        batches += 1


def maybe_cleanup_old_booking_logs(days=None, batch_size=1000, max_batches=5):
    """
    하루 1회 자동으로 오래된 로그를 정리합니다.
    초기 누적량이 많을 경우 한 요청당 최대 max_batches * batch_size건만 삭제해 응답 지연을 방지합니다.
    """
    today = date.today()
    today_key = today.isoformat()
    if cache.get(CLEANUP_DONE_DATE_KEY) == today_key:
        return 0
    if cache.get(CLEANUP_COOLDOWN_KEY):
        return 0
    if not cache.add(CLEANUP_LOCK_KEY, '1', 120):
        return 0

    try:
        deleted, has_more = cleanup_old_booking_logs(
            days=days,
            batch_size=batch_size,
            max_batches=max_batches,
            today=today,
        )
        if has_more:
            cache.set(CLEANUP_COOLDOWN_KEY, '1', 60)
        else:
            cache.set(CLEANUP_DONE_DATE_KEY, today_key, 86400)
        if deleted:
            logger.info(
                'Auto-cleaned %d old BookingLog rows (retention=%d days, has_more=%s)',
                deleted,
                get_retention_days(days),
                has_more,
            )
        return deleted
    except Exception:
        logger.exception('Auto BookingLog cleanup failed')
        return 0
    finally:
        cache.delete(CLEANUP_LOCK_KEY)
