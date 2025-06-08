from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from articleapp.decorators import staff_required
from articleapp.forms import WaitingCreationForm
from articleapp.models import Waiting, Holiday
from noteapp.models import Note
import datetime
import requests

# Create your views here.


has_ownership = [
    login_required, staff_required
]


def send_message(msg):
    DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1381414880778780682/ihbkezBF2a1u1qsWuhGMf1TQnNpVNq01K08tYJaWLUNuQl4kHTlkub3z6p3L4WMqyVeu"       #나의 디스코드 웹훅 주소
    dt_now = datetime.datetime.now()
    message = {"content": f"[{dt_now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)


# def send_message(msg):
#     TARGET_URL = 'https://notify-api.line.me/api/notify'
#     TOKEN = 'xngZHmAg4YXdRgIqMb0Rq9d7jERLOwGe1Es6jd76cJo'		# 내가 발급받은 토큰
#     headers={'Authorization': 'Bearer ' + TOKEN}
#     now = datetime.datetime.now()
#     data={'message': f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
#     response = requests.post(TARGET_URL, headers=headers, data=data)


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

    def form_valid(self, form):
        response = super().form_valid(form)  # 슈퍼클래스의 form_valid 메소드를 먼저 호출합니다.
        # waiting_num 값을 사용하여 메시지를 보냅니다.
        waiting_num = self.object.waiting_num  # self.object를 통해 생성된 Waiting 객체에 액세스합니다.
        send_message(f"선착순 대기 환자수 : {waiting_num}명")
        return response


@login_required
def HolidayPageView(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            holiday_message = request.POST.get('holiday_message')
            Holiday.objects.create(holiday_message=holiday_message)

        holiday_messages = Holiday.objects.all()
        return render(request, 'articleapp/holiday_create.html', {'holiday_messages': holiday_messages})
    elif not request.user.is_superuser:
        return redirect('articleapp:index')


class HolidayUpdateView(UpdateView):
    model = Holiday
    fields = ['holiday_message']
    template_name = 'articleapp/holiday_update.html'

    def form_valid(self, form):
        holiday_message = form.save(commit=False)
        holiday_message.save()
        return HttpResponseRedirect(reverse_lazy('articleapp:holiday_create'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holiday_message'] = self.object
        return context


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
    waiting, created = Waiting.objects.get_or_create(id=1)
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
                   'holiday_messages': holiday_messages,
                   }
    return render(request, 'articleapp/index.html', context)
