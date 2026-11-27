from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from profileapp.decorators import profile_ownership_required
from profileapp.forms import ProfileCreationForm, ProfileUpdateForm
from profileapp.models import Profile


has_ownership = [
    login_required, profile_ownership_required
]


# Create your views here.

@method_decorator(login_required, name='dispatch')
class ProfileCreateView(CreateView):
    model = Profile
    # context_object_name = 'target_profile'
    form_class = ProfileCreationForm #따로 작성이 필요함
    # success_url = reverse_lazy('accountapp:detail')
    template_name = 'profileapp/create.html'

    def form_valid(self, form):
        temp_profile = form.save(commit=False)
        temp_profile.user = self.request.user
        temp_profile.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('bookingapp:create')
        # return reverse('accountapp:detail', kwargs={'pk': self.object.user.pk})


@method_decorator(has_ownership, 'get')
@method_decorator(has_ownership, 'post')
class ProfileUpdateView(UpdateView):
    model = Profile
    # context_object_name = 'target_profile'
    form_class = ProfileUpdateForm
    # success_url = reverse_lazy('accountapp:hello_world')
    template_name = 'profileapp/update.html'

    def get_success_url(self):
        return reverse('accountapp:detail', kwargs={'pk': self.object.user.pk})