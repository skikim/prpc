from django.apps import AppConfig


class LogappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "logapp"
    verbose_name = '예약 로그'

    def ready(self):
        """앱이 준비되면 시그널을 등록합니다."""
        import logapp.signals
