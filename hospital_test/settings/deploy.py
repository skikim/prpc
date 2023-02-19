from .base import *
import environ

def read_secret(secret_name):
    file = open('/run/secrets/' + secret_name)
    secret = file.read()
    secret = secret.rstrip().lstrip()
    file.close()
    return secret


env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)



# Take environment variables from .env file
# environ.Env.read_env(os.path.join(BASE_DIR, '../../.env'))
environ.Env.read_env(os.path.join('/home/django_course', '.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = read_secret('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',
        'USER': 'prpc8575',
        'PASSWORD': read_secret('MYSQL_PASSWORD'),
        'HOST': 'mariadb',
        'PORT': '3306',
    }
}

#### Email 전송 ####
# 메일을 호스트하는 서버
EMAIL_HOST = 'smtp.gmail.com'
# gmail과의 통신하는 포트
EMAIL_PORT = '587'
# 발신할 이메일
EMAIL_HOST_USER = 'prpc8575@gmail.com'
# 발신할 메일의 비밀번호
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# TLS 보안 방법
EMAIL_USE_TLS = True
# 사이트와 관련한 자동응답을 받을 이메일 주소
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER