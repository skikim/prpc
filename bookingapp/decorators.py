from django.http import HttpResponseForbidden

from bookingapp.models import Booking

def booking_ownership_required(func):
    def decorated(request, *args, **kwargs):
        booking = Booking.objects.get(pk=kwargs['pk'])
        if not booking.user == request.user:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated