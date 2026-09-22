from django.shortcuts import redirect
from profileapp.models import Profile
from profileapp.utils import is_tablet_user


class CheckProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/bookings/create/' and request.user.is_authenticated:
            try:
                profile = Profile.objects.get(user=request.user)
                if not profile.real_name or not profile.phone_num or not profile.birth_date:
                    return redirect('profileapp:create')
            except Profile.DoesNotExist:
                return redirect('profileapp:create')
        return self.get_response(request)


class TabletKioskMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and is_tablet_user(user):
            path = request.path
            if not (
                path.startswith('/supers/tablet/')
                or path.startswith('/supers/tablet2/')
                or path.startswith('/supers/tablet3/')
                or path.startswith('/supers/waiting_pt/')
                or path.startswith('/static/')
                or path.startswith('/accounts/logout/')
            ):
                return redirect('superapp:tablet')
        return self.get_response(request)