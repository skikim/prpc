from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from articleapp.decorators import staff_required
from articleapp.forms import WaitingCreationForm
from articleapp.models import Waiting
from noteapp.models import Note

# Create your views here.

has_ownership = [
    login_required, staff_required
]

@method_decorator(has_ownership, 'get')
@method_decorator(has_ownership, 'post')
class WaitingCreateView(CreateView):
    model = Waiting
    # context_object_name = 'waitings'
    form_class = WaitingCreationForm #따로 작성이 필요함
    success_url = reverse_lazy('home')
    template_name = 'articleapp/waiting_create.html'

@method_decorator(has_ownership, 'get')
@method_decorator(has_ownership, 'post')
class WaitingUpdateView(UpdateView):
    model = Waiting
    # context_object_name = 'waitings'
    form_class = WaitingCreationForm
    success_url = reverse_lazy('home')
    template_name = 'articleapp/waiting_update.html'


def index(request):
    waiting = Waiting.objects.get(id=1)
    waiting_date = waiting.added_on_datetime.strftime('%m월 %d일')
    waiting_time = waiting.added_on_datetime.strftime('%H시 %M분')
    notes = Note.objects.filter(recipient=request.user)
    unread_notes_count = notes.filter(is_read=False).count()
    for note in notes:
        if not note.is_read:
            note.is_read = True
            note.save()
    context = {'waiting': waiting,
               'waiting_date': waiting_date,
               'waiting_time': waiting_time,
               'notes': notes,
               'unread_notes_count': unread_notes_count,
    }
    return render(request, 'articleapp/index.html', context)
