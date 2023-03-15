from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

from accountapp.views import AccountCreateView, AccountDetailView, AccountUpdateView, AccountDeleteView, AgreementView, \
    CustomLoginView

app_name = 'accountapp'

urlpatterns = [

    path('create/', AccountCreateView.as_view(), name='create'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('detail/<int:pk>', AccountDetailView.as_view(), name='detail'),
    path('update/<int:pk>', AccountUpdateView.as_view(), name='update'),
    path('delete/<int:pk>', AccountDeleteView.as_view(), name='delete'),
    path('agreement/', AgreementView.as_view(), name='agreement'),
    # path('agreement/', TemplateView.as_view(template_name='accountapp/agreement.html'), name='agreement'),

]