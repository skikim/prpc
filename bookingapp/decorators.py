from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from bookingapp.models import Booking


def booking_ownership_required(func):
    @wraps(func)
    def decorated(request, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=kwargs['pk'])
        if not booking.user == request.user:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated