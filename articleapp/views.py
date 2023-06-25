from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from articleapp.decorators import staff_required
from articleapp.forms import WaitingCreationForm
from articleapp.models import Waiting, Holiday
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
    form_class = WaitingCreationForm  # 따로 작성이 필요함
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


def HolidayPageView(request):
    if request.method == 'POST':
        holiday_message = request.POST.get('holiday_message')
        Holiday.objects.create(holiday_message=holiday_message)

    holiday_messages = Holiday.objects.all()
    return render(request, 'articleapp/holiday_create.html', {'holiday_messages': holiday_messages})


@login_required
def delete_holiday_message(request, holiday_message_id):
    holiday_message = get_object_or_404(Holiday, id=holiday_message_id)
    holiday_message.delete()
    return redirect('articleapp:holiday_create')


# @method_decorator(has_ownership, 'get')
# @method_decorator(has_ownership, 'post')
# class HolidayCreateView(CreateView):
#     model = Holiday
#     context_object_name = 'holidays'
#     form_class = HolidayCreateForm  # 따로 작성이 필요함
#     success_url = reverse_lazy('home')
#     template_name = 'articleapp/holiday_create.html'


def index(request):
    holiday_messages = Holiday.objects.all()
    waiting = Waiting.objects.get(id=1)
    waiting_date = waiting.added_on_datetime.strftime('%m월 %d일')
    waiting_time = waiting.added_on_datetime.strftime('%H시 %M분')
    if request.user.is_authenticated:
        notes = Note.objects.filter(recipient=request.user)
        notes_count = notes.count()
        unread_notes_count = notes.filter(is_read=False).count()
        for note in notes:
            if not note.is_read:
                note.is_read = True
                note.save()
        context = {'waiting': waiting,
                   'waiting_date': waiting_date,
                   'waiting_time': waiting_time,
                   'notes': notes,
                   'notes_count': notes_count,
                   'unread_notes_count': unread_notes_count,
                   'holiday_messages': holiday_messages,
                   }
    else:
        context = {'waiting': waiting,
                   'waiting_date': waiting_date,
                   'waiting_time': waiting_time,
                   }
    return render(request, 'articleapp/index.html', context)
