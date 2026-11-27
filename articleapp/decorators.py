from functools import wraps
from django.http import HttpResponseForbidden


def staff_required(func):
    @wraps(func)
    def decorated(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated


def superuser_required(func):
    @wraps(func)
    def decorated(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated
