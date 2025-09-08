"""
예약 변경 사항을 자동으로 로그에 기록하는 Django 시그널
"""
import threading
import time
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from bookingapp.models import Booking
from .models import BookingLog

# 스레드 로컬 스토리지로 현재 사용자 정보 저장
_thread_local = threading.local()

def set_current_user(user):
    """현재 요청의 사용자 정보를 설정"""
    _thread_local.user = user

def get_current_user():
    """현재 요청의 사용자 정보를 반환"""
    return getattr(_thread_local, 'user', None)

def set_request_ip(ip_address):
    """현재 요청의 IP 주소를 설정"""
    _thread_local.ip_address = ip_address

def get_request_ip():
    """현재 요청의 IP 주소를 반환"""
    return getattr(_thread_local, 'ip_address', None)

def set_booking_transition(from_status, to_status, booking_date, booking_time):
    """예약 상태 전환 정보를 설정 (delete -> create 패턴 감지용)"""
    _thread_local.booking_transition = {
        'from_status': from_status,
        'to_status': to_status, 
        'booking_date': booking_date,
        'booking_time': booking_time,
        'timestamp': time.time()
    }

def get_booking_transition():
    """예약 상태 전환 정보를 반환"""
    return getattr(_thread_local, 'booking_transition', None)


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """
    예약 수정 전 이전 상태를 저장
    """
    if instance.pk:  # 기존 객체 수정인 경우
        try:
            original = Booking.objects.get(pk=instance.pk)
            _thread_local.original_booking = original
        except Booking.DoesNotExist:
            _thread_local.original_booking = None
    else:
        _thread_local.original_booking = None


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """
    예약 생성/수정 시 로그 기록
    """
    try:
        current_user = get_current_user()
        ip_address = get_request_ip()
        
        # 중복 로그 생성 방지를 위한 체크
        if hasattr(_thread_local, 'processing_booking'):
            return
        _thread_local.processing_booking = True
        
        if created:
            # 새 예약 생성 - 전환 패턴 확인
            transition = get_booking_transition()
            if (transition and 
                transition['booking_date'] == instance.booking_date and 
                transition['booking_time'] == instance.booking_time and
                time.time() - transition['timestamp'] < 1.0):  # 1초 이내
                
                # 예약가능 → 예약요청/승인 전환
                if instance.booking_status == '예약요청':
                    action_type = 'CREATE'
                    previous_status = transition['from_status']
                    notes = f"예약 요청: {transition['from_status']} → {instance.booking_status}"
                elif instance.booking_status == '예약승인':
                    action_type = 'APPROVE'
                    previous_status = transition['from_status']
                    notes = f"예약 승인: {transition['from_status']} → {instance.booking_status}"
                else:
                    action_type = 'CREATE'
                    previous_status = transition['from_status']
                    notes = f"상태 변경: {transition['from_status']} → {instance.booking_status}"
                
                # 전환 정보 정리
                if hasattr(_thread_local, 'booking_transition'):
                    delattr(_thread_local, 'booking_transition')
            else:
                # 일반적인 새 예약 생성
                action_type = 'CREATE'
                previous_status = None
                notes = f"새 예약 생성: {instance.booking_status}"
        else:
            # 기존 예약 수정
            original = getattr(_thread_local, 'original_booking', None)
            if original and original.booking_status != instance.booking_status:
                # 상태 변경
                if instance.booking_status == '예약승인':
                    if original.booking_status == '예약요청':
                        # 예약요청 → 예약승인: 승인 로그만 생성 (예약요청 취소 로그 없음)
                        action_type = 'APPROVE'
                        notes = f"예약 승인: {original.booking_status} → {instance.booking_status}"
                    else:
                        action_type = 'UPDATE' 
                        notes = f"상태 변경: {original.booking_status} → {instance.booking_status}"
                elif instance.booking_status == '예약가능':
                    if original.booking_status in ['예약요청', '예약승인']:
                        action_type = 'DELETE'
                        notes = f"예약 취소: {original.booking_status} → {instance.booking_status}"
                    else:
                        action_type = 'UPDATE'
                        notes = f"상태 변경: {original.booking_status} → {instance.booking_status}"
                elif instance.booking_status == '예약불가':
                    if original.booking_status == '예약승인':
                        # 예약승인 → 예약불가: 예약취소로 간주
                        action_type = 'DELETE'
                        notes = f"예약 취소: {original.booking_status} → {instance.booking_status}"
                    else:
                        action_type = 'UPDATE'
                        notes = f"상태 변경: {original.booking_status} → {instance.booking_status}"
                else:
                    action_type = 'UPDATE'
                    notes = f"상태 변경: {original.booking_status} → {instance.booking_status}"
                previous_status = original.booking_status
            else:
                # 상태 변경이 없으면 로그를 생성하지 않음
                return
        
        # 로그 생성
        BookingLog.objects.create(
            booking=instance,
            action_type=action_type,
            booking_date=instance.booking_date,
            booking_time=instance.booking_time,
            user=instance.user,
            modified_by=current_user,
            previous_status=previous_status,
            new_status=instance.booking_status,
            ip_address=ip_address,
            notes=notes,
            booking_rn=instance.booking_rn
        )
        
    except Exception as e:
        # 로그 기록 실패 시에도 원본 기능에 영향을 주지 않음
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create booking log: {str(e)}")
    finally:
        # 처리 플래그 제거
        if hasattr(_thread_local, 'processing_booking'):
            delattr(_thread_local, 'processing_booking')


@receiver(post_delete, sender=Booking)
def booking_post_delete(sender, instance, **kwargs):
    """
    예약 삭제 시 로그 기록
    """
    try:
        current_user = get_current_user()
        ip_address = get_request_ip()
        
        # 예약가능 → 예약요청/승인 전환인지 확인
        if instance.booking_status == '예약가능':
            # delete -> create 패턴일 가능성이 높으므로 전환 정보 설정
            set_booking_transition(
                from_status=instance.booking_status,
                to_status=None,  # 아직 모름
                booking_date=instance.booking_date,
                booking_time=instance.booking_time
            )
            # 예약가능 삭제는 로그를 생성하지 않음 (중복 방지)
            return
        
        # 실제 예약 취소인 경우만 삭제 로그 생성
        BookingLog.objects.create(
            booking=None,  # 삭제되었으므로 None
            action_type='DELETE',
            booking_date=instance.booking_date,
            booking_time=instance.booking_time,
            user=instance.user,
            modified_by=current_user,
            previous_status=instance.booking_status,
            new_status='삭제됨',
            ip_address=ip_address,
            notes=f"예약 삭제: {instance.booking_status}에서 삭제",
            booking_rn=instance.booking_rn
        )
        
    except Exception as e:
        # 로그 기록 실패 시에도 원본 기능에 영향을 주지 않음
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create delete log: {str(e)}")