from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, TemplateView

from accountapp.decorators import account_ownership_required
from accountapp.forms import AccountUpdateForm, CreateUserForm


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

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('agreed'):
            return redirect('accountapp:agreement')
        return super().dispatch(request, *args, **kwargs)


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