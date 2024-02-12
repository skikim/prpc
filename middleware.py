from django.shortcuts import redirect
from profileapp.models import Profile


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