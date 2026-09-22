from django.contrib import admin

from articleapp.models import Waiting, Holiday, WaitingPatient


# Register your models here.

class WaitingAdmin(admin.ModelAdmin):
    list_display = ('id', 'waiting_num')
    search_fields = ['waiting_num']


class HolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'holiday_message')
    search_fields = ['holiday_message']


class WaitingPatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'visit_date', 'period', 'real_name', 'birth_date', 'created_at')
    search_fields = ['real_name', 'birth_date']


admin.site.register(Waiting, WaitingAdmin)
admin.site.register(Holiday, HolidayAdmin)
admin.site.register(WaitingPatient, WaitingPatientAdmin)
