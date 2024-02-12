from django.contrib import admin

from bookingapp.models import Booking


# Register your models here.

class BookingAdmin(admin.ModelAdmin):
    list_display=('booking_date', 'booking_time', 'user', 'booking_rn', 'booking_status', 'booked_on_datetime')
    search_fields=['booking_date', 'booking_time', 'user__username', 'booking_rn', 'booking_status', 'booked_on_datetime']

admin.site.register(Booking,BookingAdmin)