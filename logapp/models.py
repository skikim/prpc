from django.contrib.auth.models import User
from django.db import models
from bookingapp.models import Booking

class BookingLog(models.Model):
    """
    예약 변경 로그를 기록하는 모델
    """
    ACTION_TYPES = (
        ('CREATE', '예약 생성'),
        ('UPDATE', '예약 변경'),
        ('DELETE', '예약 취소'),
        ('APPROVE', '예약 승인'),
        ('REJECT', '예약 거절'),
        ('BLOCK', '예약 차단'),
        ('UNBLOCK', '예약 차단 해제'),
    )
    
    # 로그 기본 정보
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='예약')
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name='액션 타입')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='로그 생성 시간')
    
    # 예약 정보 (삭제된 경우를 위해 별도 저장)
    booking_date = models.DateField(verbose_name='예약 날짜')
    booking_time = models.CharField(max_length=16, verbose_name='예약 시간')
    
    # 변경 주체
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='booking_logs_as_user',
        verbose_name='예약자'
    )  # 예약자
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='booking_logs_as_modifier',
        verbose_name='변경자'
    )  # 변경자
    
    # 변경 내용
    previous_status = models.CharField(max_length=10, blank=True, null=True, verbose_name='이전 상태')
    new_status = models.CharField(max_length=10, verbose_name='새 상태')
    
    # 추가 정보
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP 주소')
    notes = models.TextField(blank=True, verbose_name='메모')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '예약 로그'
        verbose_name_plural = '예약 로그 목록'
    
    def __str__(self):
        action_display = dict(self.ACTION_TYPES).get(self.action_type, self.action_type)
        user_info = f"{self.user.profile.real_name if self.user and hasattr(self.user, 'profile') else self.user.username if self.user else 'N/A'}"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {action_display} - {user_info} ({self.booking_date} {self.booking_time})"
    
    def get_modifier_display(self):
        """변경자 정보를 반환"""
        if self.modified_by:
            if hasattr(self.modified_by, 'profile') and self.modified_by.profile.real_name:
                return self.modified_by.profile.real_name
            return self.modified_by.username
        return "시스템"
    
    def get_user_display(self):
        """예약자 정보를 반환"""
        if self.user:
            if hasattr(self.user, 'profile') and self.user.profile.real_name:
                return self.user.profile.real_name
            return self.user.username
        return "N/A"
    
    def get_action_display_korean(self):
        """액션 타입의 한국어 표시를 반환"""
        return dict(self.ACTION_TYPES).get(self.action_type, self.action_type)
    
    def get_simplified_action_display(self):
        """단순화된 액션 표시 - 상태 기반으로 표시"""
        if self.action_type == 'CREATE':
            if self.new_status == '예약가능':
                return '예약가능'
            elif self.new_status == '예약요청':
                return '예약요청'
            elif self.new_status == '예약승인':
                return '예약승인'
        elif self.action_type == 'APPROVE':
            return '예약승인'
        elif self.action_type == 'DELETE':
            if self.previous_status in ['예약요청', '예약승인']:
                return '예약취소'
            else:
                return '삭제'
        elif self.action_type == 'UPDATE':
            return '상태변경'
        
        return dict(self.ACTION_TYPES).get(self.action_type, self.action_type)
