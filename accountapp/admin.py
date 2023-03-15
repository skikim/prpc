from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from profileapp.models import Profile


# Register your models here.


class UserProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserProfileAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('id', 'username', 'real_name', 'phone_num', 'birth_date', 'email', 'chart_num', 'date_joined', 'is_staff',)
    ordering = ('-date_joined',)

    def real_name(self, obj):
        return obj.profile.real_name

    real_name.admin_order_field = 'profile__real_name'

    def phone_num(self, obj):
        return obj.profile.phone_num

    phone_num.admin_order_field = 'profile__phone_num'

    def birth_date(self, obj):
        return obj.profile.birth_date

    birth_date.admin_order_field = 'profile__birth_date'

    def chart_num(self, obj):
        return obj.profile.chart_num

    chart_num.admin_order_field = 'profile__chart_num'

    real_name.short_description = '이름'
    phone_num.short_description = '전화번호'
    birth_date.short_description = '생년월일'
    chart_num.short_description = '차트번호'

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        try:
            search_term = int(search_term)
            queryset |= self.model.objects.filter(profile__phone_num__contains=str(search_term))
            queryset |= self.model.objects.filter(profile__birth_date=search_term)
        except ValueError:
            queryset |= self.model.objects.filter(profile__real_name__icontains=search_term)

        return queryset.distinct(), use_distinct


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)