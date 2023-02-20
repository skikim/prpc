from django.urls import path
from django.views.generic import TemplateView

app_name = 'articleapp'

urlpatterns = [
    # path('list/', TemplateView.as_view(template_name='articleapp/list.html'), name='list'),
    path('', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),
    path('map/', TemplateView.as_view(template_name='articleapp/map.html'), name='map'),
    path('time_op/', TemplateView.as_view(template_name='articleapp/time_op.html'), name='time_op'),
    path('index/', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),
    path('pm/', TemplateView.as_view(template_name='articleapp/pain_medicine.html'), name='pm'),
    path('pm_advantage/', TemplateView.as_view(template_name='articleapp/pm_advantage.html'), name='pm_advantage'),
    path('pm_disease/', TemplateView.as_view(template_name='articleapp/pm_disease.html'), name='pm_disease'),
    path('privacy_concent/', TemplateView.as_view(template_name='articleapp/privacy_concent.html'), name='privacy_concent'),

]