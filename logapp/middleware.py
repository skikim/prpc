"""
현재 요청의 사용자 정보를 시그널에서 사용할 수 있도록 하는 미들웨어
"""
from .signals import set_current_user, set_request_ip


class LoggingMiddleware:
    """
    현재 요청의 사용자와 IP 정보를 스레드 로컬에 저장하는 미들웨어
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 요청 시작 시 사용자 정보 설정
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        set_current_user(user)
        
        # IP 주소 설정
        ip_address = self.get_client_ip(request)
        set_request_ip(ip_address)

        response = self.get_response(request)

        # 요청 완료 후 정리 (선택사항)
        set_current_user(None)
        set_request_ip(None)

        return response

    def get_client_ip(self, request):
        """클라이언트의 실제 IP 주소를 반환"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip