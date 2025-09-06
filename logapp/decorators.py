from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

def superuser_required(view_func):
    """
    수퍼유저만 접근할 수 있는 뷰에 사용하는 데코레이터
    로그인도 함께 확인합니다.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("수퍼유저만 접근 가능합니다.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ajax_superuser_required(view_func):
    """
    AJAX 요청에서 수퍼유저 권한을 확인하는 데코레이터
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.http import JsonResponse
            return JsonResponse({'error': '수퍼유저만 접근 가능합니다.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view