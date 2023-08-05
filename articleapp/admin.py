from django.contrib import admin

from articleapp.models import Waiting, Holiday


# Register your models here.

class WaitingAdmin(admin.ModelAdmin):
    list_display = ('id', 'waiting_num')
    search_fields = ['waiting_num']


class HolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'holiday_message')
    search_fields = ['holiday_message']


admin.site.register(Waiting, WaitingAdmin)
admin.site.register(Holiday, HolidayAdmin)
