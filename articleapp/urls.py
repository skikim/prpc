from django.urls import path
from django.views.generic import TemplateView

from articleapp.views import WaitingCreateView, WaitingUpdateView, index, HolidayPageView, delete_holiday_message, \
    HolidayUpdateView

app_name = 'articleapp'

urlpatterns = [
    # path('list/', TemplateView.as_view(template_name='articleapp/list.html'), name='list'),
    # path('', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),
    path('', index, name='index'),
    path('movie/', TemplateView.as_view(template_name='articleapp/movie.html'), name='movie'),
    path('map/', TemplateView.as_view(template_name='articleapp/map.html'), name='map'),
    path('time_op/', TemplateView.as_view(template_name='articleapp/time_op.html'), name='time_op'),
    path('index/', index, name='index'),
    path('pm/', TemplateView.as_view(template_name='articleapp/pain_medicine.html'), name='pm'),
    path('pm_advantage/', TemplateView.as_view(template_name='articleapp/pm_advantage.html'), name='pm_advantage'),
    path('pm_disease/', TemplateView.as_view(template_name='articleapp/pm_disease.html'), name='pm_disease'),
    path('privacy_concent/', TemplateView.as_view(template_name='articleapp/privacy_concent.html'), name='privacy_concent'),
    path('cctv/', TemplateView.as_view(template_name='articleapp/cctv.html'), name='cctv'),
    path('price/', TemplateView.as_view(template_name='articleapp/price.html'), name='price'),
    path('waiting_create/', WaitingCreateView.as_view(), name='waiting_create'),
    path('waiting_update/<int:pk>', WaitingUpdateView.as_view(), name='waiting_update'),
    path('holiday_create/', HolidayPageView, name='holiday_create'),
    path('holiday_message_delete/<int:holiday_message_id>/', delete_holiday_message, name='holiday_message_delete'),
    path('holiday_update/<int:pk>/', HolidayUpdateView.as_view(), name='holiday_update'),
]