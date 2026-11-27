from functools import wraps
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404


def account_ownership_required(func):
    @wraps(func)
    def decorated(request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        if not user == request.user:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated