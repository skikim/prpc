from django.contrib import admin
from .models import BookingLog


@admin.register(BookingLog)
class BookingLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'action_type', 'booking_date', 'booking_time', 
        'get_user_display', 'get_modifier_display', 'new_status'
    )
    list_filter = (
        'action_type', 'booking_date', 'new_status', 'created_at'
    )
    search_fields = (
        'user__username', 'user__profile__real_name',
        'modified_by__username', 'modified_by__profile__real_name',
        'booking_date', 'booking_time', 'notes'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = (
        'booking', 'action_type', 'created_at', 'booking_date', 'booking_time',
        'user', 'modified_by', 'previous_status', 'new_status', 'ip_address', 'notes'
    )
    
    def has_add_permission(self, request):
        """로그는 수동으로 추가할 수 없습니다."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """로그는 수정할 수 없습니다."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """로그는 삭제할 수 없습니다."""
        return False
