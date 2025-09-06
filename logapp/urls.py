from django.urls import path
from . import views

app_name = 'logapp'

urlpatterns = [
    # 로그 목록 조회 (메인 페이지)
    path('', views.log_list, name='log_list'),
    
    # 검색 페이지
    path('search/', views.log_search, name='log_search'),
    
    # AJAX 검색 API
    path('api/search/', views.log_search_api, name='log_search_api'),
    
    # 특정 날짜/시간 예약 로그 조회
    path('booking/<str:date>/<str:time>/', views.booking_log_detail, name='booking_log_detail'),
    
    # 특정 사용자 로그 조회
    path('user/<int:user_id>/', views.user_log_detail, name='user_log_detail'),
]