from django.urls import path
from django.views.generic import TemplateView

app_name = 'articleapp'

urlpatterns = [
    # path('list/', TemplateView.as_view(template_name='articleapp/list.html'), name='list'),
    path('', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),
    path('map/', TemplateView.as_view(template_name='articleapp/map.html'), name='map'),
    path('time_op/', TemplateView.as_view(template_name='articleapp/time_op.html'), name='time_op'),
    path('index/', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),

]