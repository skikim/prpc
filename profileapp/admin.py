from django.contrib import admin

from profileapp.models import Profile

# Register your models here.

class profileAdmin(admin.ModelAdmin):
    list_display=('user', 'real_name', 'birth_date', 'phone_num', 'chart_num')
    search_fields=['real_name', 'birth_date', 'phone_num', 'chart_num']

admin.site.register(Profile, profileAdmin)
