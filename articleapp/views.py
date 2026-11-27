from bs4 import BeautifulSoup, Comment
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import hashlib
import json

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

from articleapp.decorators import staff_required, superuser_required
from articleapp.forms import WaitingCreationForm
from articleapp.models import Waiting, Holiday
from articleapp.waiting_utils import (
    MAX_WAITING,
    active_manual_override,
    active_notice_period,
    clear_manual_waiting_override,
    homepage_waiting,
    homepage_waiting_payload,
    local_now,
    notice_sessions,
    period_label,
    set_manual_waiting_override,
    waiting_clock_text,
    waiting_count,
)
from noteapp.models import Note
import datetime
from superapp.utils import send_discord_message
import re

# Create your views here.


ALLOWED_HOLIDAY_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'span', 'div',
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
}
STRIP_HOLIDAY_TAGS = {
    'script', 'style', 'iframe', 'object', 'embed', 'svg', 'math',
    'noscript', 'template', 'head', 'title', 'textarea', 'xmp',
}
ALLOWED_CSS_PROPS = {
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-decoration', 'text-align', 'margin', 'margin-top', 'margin-bottom',
    'padding', 'padding-left', 'line-height',
}
SAFE_CSS_VALUE_RE = re.compile(r'^[#a-zA-Z0-9\s.,()%+-]+$')
DANGEROUS_CSS_RE = re.compile(r'(?i)(url\s*\(|expression\s*\(|javascript:|vbscript:|behavior:|@import)')


def _sanitize_style(style_value):
    if not style_value:
        return ''
    safe_parts = []
    for decl in str(style_value).split(';'):
        if ':' not in decl:
            continue
        prop, val = decl.split(':', 1)
        prop = prop.strip().lower()
        val = val.strip()
        if prop not in ALLOWED_CSS_PROPS or not val:
            continue
        if DANGEROUS_CSS_RE.search(val) or not SAFE_CSS_VALUE_RE.fullmatch(val):
            continue
        safe_parts.append(f'{prop}: {val}')
    return '; '.join(safe_parts)


def sanitize_holiday_html(html):
    if not html:
        return html
    soup = BeautifulSoup(html, 'html.parser')
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in list(soup.find_all(True)):
        if tag.parent is None:
            continue
        name = (tag.name or '').lower()
        if name in STRIP_HOLIDAY_TAGS:
            tag.decompose()
            continue
        if name not in ALLOWED_HOLIDAY_TAGS:
            tag.unwrap()
            continue
        clean_attrs = {}
        if 'style' in tag.attrs:
            safe_style = _sanitize_style(tag.attrs.get('style'))
            if safe_style:
                clean_attrs['style'] = safe_style
        tag.attrs = clean_attrs
    return str(soup)


has_ownership = [
    login_required, staff_required
]

has_superuser = [
    login_required, superuser_required
]


# Discord 알림 함수는 superapp.utils로 이동되었습니다.


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

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is None or pk == 1:
            waiting, _ = Waiting.objects.get_or_create(id=1)
            return waiting
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = local_now()
        period = active_notice_period(now)
        live_count = waiting_count(now.date(), period) if period else 0
        display = homepage_waiting(now, self.object.added_on_datetime, self.object.waiting_num, waiting=self.object)
        override = active_manual_override(self.object, now)
        if override is not None:
            initial_num = override['number']
        elif display['visible']:
            initial_num = display['number']
        else:
            initial_num = min(live_count, MAX_WAITING)
        context.update({
            'period': period,
            'period_label': period_label(period),
            'live_count': live_count,
            'live_display_count': min(live_count, MAX_WAITING),
            'display': display,
            'display_clock': waiting_clock_text(display['clock']) if display['visible'] else '',
            'override_active': override is not None,
            'override_num': override['number'] if override is not None else None,
            'override_clock': waiting_clock_text(override['clock']) if override is not None else '',
            'initial_num': initial_num,
            'max_waiting': MAX_WAITING,
            'waiting_choices': range(MAX_WAITING + 1),
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        now = local_now()
        action = request.POST.get('action', 'override')
        if action == 'reset':
            had_override = active_manual_override(self.object, now) is not None
            clear_manual_waiting_override(self.object)
            period = active_notice_period(now)
            if had_override:
                if period:
                    live = min(waiting_count(now.date(), period), MAX_WAITING)
                    send_discord_message(f"선착순 대기 환자수 자동 복귀 : {live}명")
                else:
                    send_discord_message("선착순 대기 환자수 강제 변경 해제")
            messages.success(request, '강제 변경을 해제하고 태블릿 대기 인원으로 복귀했습니다.')
            return redirect(request.path)

        raw_num = (request.POST.get('waiting_num') or '').strip()
        try:
            waiting_num = int(raw_num)
        except ValueError:
            messages.error(request, f'대기 환자수는 0부터 {MAX_WAITING} 사이의 숫자로 입력해 주세요.')
            return redirect(request.path)
        if waiting_num < 0 or waiting_num > MAX_WAITING:
            messages.error(request, f'대기 환자수는 0부터 {MAX_WAITING} 사이의 숫자로 입력해 주세요.')
            return redirect(request.path)

        if not set_manual_waiting_override(self.object, waiting_num, now=now):
            messages.warning(
                request,
                '현재는 선착순 대기 안내 시간(오전 06:30~09:10, 오후 11:30~14:10)이 아닙니다. 안내 시간 중에 강제 변경을 적용해 주세요.',
            )
            return redirect(request.path)

        send_discord_message(f"선착순 대기 환자수(수동 강제 변경) : {waiting_num}명")
        messages.success(request, f'홈 화면 대기 환자수를 {waiting_num}명으로 강제 변경했습니다.')
        return redirect(request.path)


@login_required
def HolidayPageView(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            holiday_message = sanitize_holiday_html(request.POST.get('holiday_message'))
            Holiday.objects.create(holiday_message=holiday_message)

        holiday_messages = Holiday.objects.all()
        return render(request, 'articleapp/holiday_create.html', {'holiday_messages': holiday_messages})
    elif not request.user.is_superuser:
        return redirect('articleapp:index')


@method_decorator(has_superuser, name='dispatch')
class HolidayUpdateView(UpdateView):
    model = Holiday
    fields = ['holiday_message']
    template_name = 'articleapp/holiday_update.html'

    def form_valid(self, form):
        holiday_message = form.save(commit=False)
        holiday_message.holiday_message = sanitize_holiday_html(holiday_message.holiday_message)
        holiday_message.save()
        return HttpResponseRedirect(reverse_lazy('articleapp:holiday_create'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holiday_message'] = self.object
        return context


@login_required
@superuser_required
@require_POST
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


def waiting_status(request):
    payload = homepage_waiting_payload(local_now())
    encoded = json.dumps(payload, separators=(',', ':'), ensure_ascii=False, sort_keys=True).encode('utf-8')
    etag = '"' + hashlib.sha1(encoded).hexdigest() + '"'
    if request.META.get('HTTP_IF_NONE_MATCH') == etag:
        response = HttpResponse(status=304)
    else:
        response = JsonResponse(payload)
    response['ETag'] = etag
    response['Cache-Control'] = 'private, no-cache'
    return response


def index(request):
    holiday_messages = Holiday.objects.all()
    waiting, created = Waiting.objects.get_or_create(id=1)
    waiting_date = waiting.added_on_datetime.strftime('%m월 %d일')
    waiting_time = waiting.added_on_datetime.strftime('%H시 %M분')
    clock = waiting.added_on_datetime
    waiting_clock = waiting_clock_text(clock)
    now = local_now()
    sessions = notice_sessions(now)
    notice_am = 'am' in sessions
    notice_pm = 'pm' in sessions
    display = homepage_waiting(now, waiting.added_on_datetime, waiting.waiting_num, waiting=waiting)
    waiting_notice = display['visible']
    waiting_display_num = display['number']
    notice_period = display['period']
    if display['clock']:
        waiting_clock = waiting_clock_text(display['clock'])
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
                   'waiting_clock': waiting_clock,
                   'notes': notes,
                   'notes_count': notes_count,
                   'unread_notes_count': unread_notes_count,
                   'holiday_messages': holiday_messages,
                   'notice_am': notice_am,
                   'notice_pm': notice_pm,
                   'notice_period': notice_period,
                   'waiting_notice': waiting_notice,
                   'waiting_display_num': waiting_display_num,
                   }
    else:
        context = {'waiting': waiting,
                   'waiting_date': waiting_date,
                   'waiting_time': waiting_time,
                   'waiting_clock': waiting_clock,
                   'holiday_messages': holiday_messages,
                   'notice_am': notice_am,
                   'notice_pm': notice_pm,
                   'notice_period': notice_period,
                   'waiting_notice': waiting_notice,
                   'waiting_display_num': waiting_display_num,
                   }
    return render(request, 'articleapp/index.html', context)
