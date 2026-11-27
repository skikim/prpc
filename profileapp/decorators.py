from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from profileapp.models import Profile


def profile_ownership_required(func):
    @wraps(func)
    def decorated(request, *args, **kwargs):
        profile = get_object_or_404(Profile, pk=kwargs['pk'])
        if not profile.user == request.user:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return decorated