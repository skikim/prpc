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

        try:
            return self.get_response(request)
        finally:
            # 요청 완료 또는 예외 발생 시 스레드 로컬 정리 보장
            set_current_user(None)
            set_request_ip(None)

    def get_client_ip(self, request):
        """신뢰 가능한 프록시 헤더를 우선하여 클라이언트의 실제 IP 주소를 반환"""
        x_real_ip = (request.META.get('HTTP_X_REAL_IP') or '').strip()
        if x_real_ip:
            return x_real_ip
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            parts = [part.strip() for part in x_forwarded_for.split(',') if part.strip()]
            if parts:
                return parts[-1]
        return request.META.get('REMOTE_ADDR')