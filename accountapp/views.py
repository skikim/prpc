from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, TemplateView, FormView

from accountapp.decorators import account_ownership_required
from accountapp.forms import AccountUpdateForm, CreateUserForm
from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm
# from .forms import CustomUserCreationForm


has_ownership = [
    login_required, account_ownership_required
]
# Create your views here.


class AgreementView(TemplateView):
    template_name = 'accountapp/agreement.html'

    def post(self, request, *args, **kwargs):
        request.session['agreed'] = True
        return redirect('accountapp:create')


class AccountCreateView(CreateView):
    model = User
    form_class = CreateUserForm
    # form_class = UserCreationForm
    success_url = reverse_lazy('accountapp:login')
    template_name = 'accountapp/create.html'

    def form_valid(self, form):
        # terms_agreement 필드는 폼에서 자동으로 유효성 검사됨
        # required=True이므로 체크하지 않으면 폼 에러 발생
        return super().form_valid(form)


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'accountapp/login.html'


@method_decorator(account_ownership_required, 'get')
class AccountDetailView(DetailView):
    model = User
    # context_object_name = 'target_user'
    template_name = 'accountapp/detail.html'


@method_decorator(has_ownership, 'get')
@method_decorator(has_ownership, 'post')
class AccountUpdateView(UpdateView):
    model = User
    # context_object_name = 'target_user'
    form_class = AccountUpdateForm
    success_url = reverse_lazy('accountapp:login')
    template_name = 'accountapp/update.html'


@method_decorator(has_ownership, 'get')
@method_decorator(has_ownership, 'post')
class AccountDeleteView(DeleteView):
    model = User
    # context_object_name = 'target_user'
    success_url = reverse_lazy('articleapp:index')
    template_name = 'accountapp/delete.html'