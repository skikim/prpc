"""hospital_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

import articleapp
from articleapp.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accountapp.urls')),
    path('profiles/', include('profileapp.urls')),
    path('articles/', include('articleapp.urls')),
    path('bookings/', include('bookingapp.urls')),
    path('supers/', include('superapp.urls')),
    path('passwords/', include('passwordapp.urls')),
    path('', articleapp.views.index, name='index'),
    path('home/', articleapp.views.index, name='home'),

    # path('', TemplateView.as_view(template_name='articleapp/index.html'), name='index'),
    # path('home/', TemplateView.as_view(template_name='articleapp/index.html'), name='home'),
]
