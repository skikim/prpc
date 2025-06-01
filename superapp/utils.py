"""
예약 차단 기능을 위한 유틸리티 함수들
"""
import datetime
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from bookingapp.models import Booking
import logging

logger = logging.getLogger(__name__)

# 캐시 키 네이밍 규칙
BOOKING_BLOCK_KEY_PREFIX = "booking_block"
BOOKING_BLOCK_STATUS_KEY = "booking_block_status"


def get_booking_block_key(booking_date, booking_time):
    """
    특정 예약 시간대의 차단 캐시 키를 생성합니다.
    
    Args:
        booking_date (str): 예약 날짜 (YYYY-MM-DD 형식)
        booking_time (str): 예약 시간 (HH:MM 형식)
    
    Returns:
        str: 캐시 키
    """
    return f"{BOOKING_BLOCK_KEY_PREFIX}_{booking_date}_{booking_time}"


def is_booking_blocked(booking_date, booking_time):
    """
    특정 예약 시간대가 차단되어 있는지 확인합니다.
    
    Args:
        booking_date (str): 예약 날짜 (YYYY-MM-DD 형식)
        booking_time (str): 예약 시간 (HH:MM 형식)
    
    Returns:
        bool: 차단되어 있으면 True, 아니면 False
    """
    cache_key = get_booking_block_key(booking_date, booking_time)
    return cache.get(cache_key) is not None


def block_booking_slot(booking_date, booking_time, user_id=None):
    """
    특정 예약 시간대를 차단합니다.
    
    Args:
        booking_date (str): 예약 날짜 (YYYY-MM-DD 형식)
        booking_time (str): 예약 시간 (HH:MM 형식)
        user_id (int, optional): 차단을 요청한 사용자 ID
    
    Returns:
        bool: 성공하면 True, 실패하면 False
    """
    try:
        cache_key = get_booking_block_key(booking_date, booking_time)
        block_data = {
            'blocked_at': datetime.datetime.now().isoformat(),
            'blocked_by': user_id,
            'booking_date': booking_date,
            'booking_time': booking_time,
        }
        
        timeout = getattr(settings, 'BOOKING_BLOCK_TIMEOUT', 180)
        cache.set(cache_key, block_data, timeout)
        
        logger.info(f"Booking slot blocked: {booking_date} {booking_time} by user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to block booking slot {booking_date} {booking_time}: {str(e)}")
        return False


def unblock_booking_slot(booking_date, booking_time):
    """
    특정 예약 시간대의 차단을 해제합니다.
    
    Args:
        booking_date (str): 예약 날짜 (YYYY-MM-DD 형식)
        booking_time (str): 예약 시간 (HH:MM 형식)
    
    Returns:
        bool: 성공하면 True, 실패하면 False
    """
    try:
        cache_key = get_booking_block_key(booking_date, booking_time)
        cache.delete(cache_key)
        
        logger.info(f"Booking slot unblocked: {booking_date} {booking_time}")
        return True
    except Exception as e:
        logger.error(f"Failed to unblock booking slot {booking_date} {booking_time}: {str(e)}")
        return False


def get_available_bookings_for_period(days=None):
    """
    지정된 기간 내의 예약 가능한 시간대를 조회합니다.
    
    Args:
        days (int, optional): 조회할 기간 (일 단위). 기본값은 설정에서 가져옴
    
    Returns:
        QuerySet: 예약 가능한 Booking 객체들
    """
    if days is None:
        days = getattr(settings, 'BOOKING_BLOCK_PERIOD_DAYS', 14)
    
    today = datetime.date.today()
    end_date = today + timedelta(days=days)
    
    return Booking.objects.filter(
        booking_date__gte=today,
        booking_date__lte=end_date,
        booking_status='예약가능'
    )


def block_all_available_bookings(user_id=None):
    """
    설정된 기간 내의 모든 예약 가능한 시간대를 차단합니다.
    
    Args:
        user_id (int, optional): 차단을 요청한 사용자 ID
    
    Returns:
        dict: 결과 정보 (성공 수, 실패 수, 총 수)
    """
    available_bookings = get_available_bookings_for_period()
    
    success_count = 0
    fail_count = 0
    total_count = available_bookings.count()
    
    for booking in available_bookings:
        booking_date_str = booking.booking_date.strftime('%Y-%m-%d')
        if block_booking_slot(booking_date_str, booking.booking_time, user_id):
            success_count += 1
        else:
            fail_count += 1
    
    # 전체 차단 상태 정보 저장
    block_status = {
        'blocked_at': datetime.datetime.now().isoformat(),
        'blocked_by': user_id,
        'total_slots': total_count,
        'success_count': success_count,
        'fail_count': fail_count,
    }
    
    timeout = getattr(settings, 'BOOKING_BLOCK_TIMEOUT', 180)
    cache.set(BOOKING_BLOCK_STATUS_KEY, block_status, timeout)
    
    logger.info(f"Bulk booking block completed: {success_count}/{total_count} slots blocked by user {user_id}")
    
    return {
        'total': total_count,
        'success': success_count,
        'failed': fail_count,
    }


def unblock_all_bookings():
    """
    모든 차단된 예약 시간대를 해제합니다.
    
    Returns:
        bool: 성공하면 True, 실패하면 False
    """
    try:
        # 현재 차단된 모든 키를 찾아서 삭제
        # 주의: 이 방법은 캐시 백엔드에 따라 다를 수 있음
        available_bookings = get_available_bookings_for_period()
        
        for booking in available_bookings:
            booking_date_str = booking.booking_date.strftime('%Y-%m-%d')
            unblock_booking_slot(booking_date_str, booking.booking_time)
        
        # 전체 차단 상태 정보도 삭제
        cache.delete(BOOKING_BLOCK_STATUS_KEY)
        
        logger.info("All booking blocks removed")
        return True
    except Exception as e:
        logger.error(f"Failed to unblock all bookings: {str(e)}")
        return False


def get_block_status():
    """
    현재 차단 상태 정보를 조회합니다.
    
    Returns:
        dict or None: 차단 상태 정보
    """
    return cache.get(BOOKING_BLOCK_STATUS_KEY)


def get_blocked_slots():
    """
    현재 차단된 모든 시간대 목록을 조회합니다.
    
    Returns:
        list: 차단된 시간대 정보 리스트
    """
    blocked_slots = []
    available_bookings = get_available_bookings_for_period()
    
    for booking in available_bookings:
        booking_date_str = booking.booking_date.strftime('%Y-%m-%d')
        if is_booking_blocked(booking_date_str, booking.booking_time):
            cache_key = get_booking_block_key(booking_date_str, booking.booking_time)
            block_data = cache.get(cache_key)
            if block_data:
                blocked_slots.append({
                    'booking_date': booking_date_str,
                    'booking_time': booking.booking_time,
                    'blocked_at': block_data.get('blocked_at'),
                    'blocked_by': block_data.get('blocked_by'),
                })
    
    return blocked_slots 