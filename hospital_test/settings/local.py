from .base import *
import environ


env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Take environment variables from .env file
# environ.Env.read_env(os.path.join(BASE_DIR, '../../.env'))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

#### Email 전송 ####
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 메일을 호스트하는 서버
EMAIL_HOST = 'smtp.naver.com'
# gmail과의 통신하는 포트
EMAIL_PORT = '465'
# 발신할 이메일
EMAIL_HOST_USER = 'prpc8575@naver.com'
# 발신할 메일의 비밀번호
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# TLS 보안 방법
# EMAIL_USE_TLS = True
EMAIL_USE_SSL = True
# 사이트와 관련한 자동응답을 받을 이메일 주소
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER