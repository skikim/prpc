from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'searchapp'

urlpatterns = [
    path('search/', views.search, name='search'),
]