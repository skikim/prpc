from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

def staff_required(func):
    def decorated(request, *args, **kwargs):
        # user = User.objects.get
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated