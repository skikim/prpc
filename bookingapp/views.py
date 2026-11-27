import datetime
from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

from articleapp.models import Holiday
from bookingapp.decorators import booking_ownership_required
from bookingapp.models import Booking
import requests

from noteapp.models import Note
from django.contrib.auth.models import User
from profileapp.utils import is_tablet_user
from superapp.utils import chart_key, is_booking_blocked, same_day_slots, send_discord_message_both
from superapp.views import sync_tablet_week_screen


def delete_approval_messages(user, booking_date, booking_time):
    """예약 취소/변경 시 기존 승인 메시지를 삭제하는 공통 함수"""
    if user and user.profile:
        approval_message_pattern = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
        deleted_count = Note.objects.filter(
            recipient_id=user.id,
            message=approval_message_pattern
        ).delete()[0]
        return deleted_count
    return 0


# Create your views here.

has_ownership = [
    login_required, booking_ownership_required
]


# Discord 알림 함수들은 superapp.utils로 이동되었습니다.


MAX_ONLINE_BOOKING_DAYS = 14


def _validate_online_booking_date(booking_date):
    if not booking_date:
        return None, '올바른 예약 날짜를 선택해 주세요.'
    try:
        booking_date_obj = datetime.datetime.strptime(booking_date, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None, '올바른 예약 날짜를 선택해 주세요.'
    today = datetime.date.today()
    if booking_date_obj < today:
        return None, '지난 날짜는 예약할 수 없습니다.'
    if booking_date_obj > today + timedelta(days=MAX_ONLINE_BOOKING_DAYS):
        return None, '온라인 예약은 오늘부터 2주 이내의 날짜만 가능합니다.'
    return booking_date_obj, None


def _reserve_online_slot(user, request_real_name, patient_chart, booking_date, booking_date_obj, booking_time, conflict_message):
    days_since_sunday = (booking_date_obj.weekday() + 1) % 7
    week_start = booking_date_obj - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)

    with transaction.atomic():
        if same_day_slots(user.id, patient_chart, booking_date_obj):
            return False, '온라인 예약은 하루에 1회만 가능합니다.'

        weekly_bookings = Booking.objects.filter(
            Q(user=user),
            Q(booking_date__range=(week_start, week_end)),
            Q(booking_status='예약승인') | Q(booking_status='예약요청'),
        )
        logger.info(f"주2회 예약 체크 - 사용자: {user.username}(ID:{user.id}), 주간범위: {week_start} ~ {week_end}, 기존 예약 수: {weekly_bookings.count()}")
        if weekly_bookings.count() >= 2:
            logger.info(f"주2회 예약 제한 - 사용자: {user.username}, 이미 {weekly_bookings.count()}개의 예약 존재")
            return False, '온라인 예약은 주 2회만 가능합니다.'

        if is_booking_blocked(booking_date, booking_time):
            logger.info(f"예약 차단됨 - 날짜/시간: {booking_date} {booking_time}")
            return False, '현재 병원에서 다른 환자의 예약이 진행 중이어서 요청하신 시간의 온라인 예약이 불가능합니다. 잠시 후 다시 시도해 주십시오.'

        selected_booking = Booking.objects.select_for_update().filter(
            booking_date=booking_date,
            booking_time=booking_time,
        ).first()
        if selected_booking is None or selected_booking.booking_status != '예약가능':
            status_val = selected_booking.booking_status if selected_booking else '없음'
            logger.info(f"예약 실패 - 선택된 예약 상태: {status_val}")
            return False, conflict_message

        selected_booking.delete()
        new_booking = Booking(
            booking_date=booking_date,
            booking_time=booking_time,
            user=user,
            booking_status='예약요청',
        )
        new_booking.save()
        logger.info(f"예약 성공 - 새 예약ID: {new_booking.pk}, 사용자: {user.username}, 날짜/시간: {booking_date} {booking_time}")

    send_discord_message_both(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
    return True, None


@login_required
def booking(request):
    if request.method == 'GET':
        sync_tablet_week_screen(request, 'week1')
    today_1 = datetime.datetime.now() - timedelta(hours=9)
    today_2 = today_1 + timedelta(days=1)
    today_3 = today_1 + timedelta(days=2)
    today_4 = today_1 + timedelta(days=3)
    today_5 = today_1 + timedelta(days=4)
    today_6 = today_1 + timedelta(days=5)
    today_7 = today_1 + timedelta(days=6)
    inform_today_1 = Booking.objects.filter(booking_date = today_1.strftime('%Y-%m-%d'))
    inform_today_2 = Booking.objects.filter(booking_date = today_2.strftime('%Y-%m-%d'))
    inform_today_3 = Booking.objects.filter(booking_date = today_3.strftime('%Y-%m-%d'))
    inform_today_4 = Booking.objects.filter(booking_date = today_4.strftime('%Y-%m-%d'))
    inform_today_5 = Booking.objects.filter(booking_date = today_5.strftime('%Y-%m-%d'))
    inform_today_6 = Booking.objects.filter(booking_date = today_6.strftime('%Y-%m-%d'))
    inform_today_7 = Booking.objects.filter(booking_date = today_7.strftime('%Y-%m-%d'))

    context = {'inform_today_1': inform_today_1,
               'inform_today_2': inform_today_2,
               'inform_today_3': inform_today_3,
               'inform_today_4': inform_today_4,
               'inform_today_5': inform_today_5,
               'inform_today_6': inform_today_6,
               'inform_today_7': inform_today_7,
    }

    errors = []
    if request.method == 'POST':
        if is_tablet_user(request.user):
            return redirect('bookingapp:create')
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        user = request.user
        booking_date_obj, date_error = _validate_online_booking_date(booking_date)
        if date_error:
            errors.append(date_error)
            return render(request, 'bookingapp/post_write.html', {'errors': errors})
        try:
            request_real_name = request.user.profile.real_name
            patient_chart = chart_key(request.user.profile.chart_num)
        except Exception:
            return redirect(reverse('profileapp:create'))

        ok, err = _reserve_online_slot(
            user,
            request_real_name,
            patient_chart,
            booking_date,
            booking_date_obj,
            booking_time,
            '안타깝게도 예약하시는 사이 다른 분이 먼저 예약요청 버튼을 누르셨습니다. 다른 시간대를 선택해서 예약요청해 주세요.',
        )
        if ok:
            return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
        errors.append(err)
        return render(request, 'bookingapp/post_write.html', {'errors': errors})
    return render(request, 'bookingapp/create.html', context)


@login_required
def booking_2(request):
    if request.method == 'GET':
        sync_tablet_week_screen(request, 'week2')
    today_1 = datetime.datetime.now() - timedelta(hours=9)
    today_8 = today_1 + timedelta(days=7)
    today_9 = today_1 + timedelta(days=8)
    today_10 = today_1 + timedelta(days=9)
    today_11 = today_1 + timedelta(days=10)
    today_12 = today_1 + timedelta(days=11)
    today_13 = today_1 + timedelta(days=12)
    today_14 = today_1 + timedelta(days=13)
    inform_today_8 = Booking.objects.filter(booking_date = today_8.strftime('%Y-%m-%d'))
    inform_today_9 = Booking.objects.filter(booking_date = today_9.strftime('%Y-%m-%d'))
    inform_today_10 = Booking.objects.filter(booking_date = today_10.strftime('%Y-%m-%d'))
    inform_today_11 = Booking.objects.filter(booking_date = today_11.strftime('%Y-%m-%d'))
    inform_today_12 = Booking.objects.filter(booking_date = today_12.strftime('%Y-%m-%d'))
    inform_today_13 = Booking.objects.filter(booking_date = today_13.strftime('%Y-%m-%d'))
    inform_today_14 = Booking.objects.filter(booking_date = today_14.strftime('%Y-%m-%d'))

    context = {'inform_today_8': inform_today_8,
               'inform_today_9': inform_today_9,
               'inform_today_10': inform_today_10,
               'inform_today_11': inform_today_11,
               'inform_today_12': inform_today_12,
               'inform_today_13': inform_today_13,
               'inform_today_14': inform_today_14,
    }
    errors = []
    if request.method == 'POST':
        if is_tablet_user(request.user):
            return redirect('bookingapp:create2')
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        user = request.user
        booking_date_obj, date_error = _validate_online_booking_date(booking_date)
        if date_error:
            errors.append(date_error)
            return render(request, 'bookingapp/post_write.html', {'errors': errors})
        try:
            request_real_name = request.user.profile.real_name
            patient_chart = chart_key(request.user.profile.chart_num)
        except Exception:
            return redirect(reverse('profileapp:create'))

        ok, err = _reserve_online_slot(
            user,
            request_real_name,
            patient_chart,
            booking_date,
            booking_date_obj,
            booking_time,
            '예약하시는 동안 다른 분이 먼저 예약요청 버튼을 누르셨습니다. 다른 시간대를 선택해서 예약요청해 주세요.',
        )
        if ok:
            return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
        errors.append(err)
        return render(request, 'bookingapp/post_write.html', {'errors': errors})
    return render(request, 'bookingapp/create_2.html', context)




class BookingDetailView(DetailView):
    model = Booking
    context_object_name = 'user'
    template_name = 'bookingapp/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today_date = datetime.date.today()
        context['today'] = today_date
        return context

    def get_object(self):
        return self.request.user

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated and self.get_object() == self.request.user:
            return super().get(*args, **kwargs)
        else:
            return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        if self.request.user.is_authenticated and self.get_object() == self.request.user:
            return super().post(*args, **kwargs)
        else:
            return HttpResponseForbidden()


@login_required
@booking_ownership_required
def booking_delete(request, pk):
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M")
    booking = get_object_or_404(Booking, pk=pk)
    booking_date = booking.booking_date
    booking_time = booking.booking_time
    booking_status = '예약가능'
    request_real_name = booking.user.profile.real_name
    request_user_id = booking.user_id
    if booking.is_past():
        messages.error(request, '지난 예약은 취소할 수 없습니다.')
        return redirect(reverse('bookingapp:detail', kwargs={'pk': booking.user.pk}))
    if request.method == 'POST':
        with transaction.atomic():
            locked_booking = Booking.objects.select_for_update().filter(pk=pk, user=request.user).first()
            if locked_booking is None:
                return redirect(reverse('bookingapp:detail', kwargs={'pk': request.user.pk}))
            logger.info(f"예약 취소 시작 - 사용자: {request_real_name}(ID:{request_user_id}), 예약ID: {locked_booking.pk}, 날짜/시간: {booking_date} {booking_time}, 상태: {locked_booking.booking_status}")

            delete_approval_messages(locked_booking.user, booking_date, booking_time)
            locked_booking.delete()
            logger.info(f"기존 예약 삭제 완료 - 예약ID: {pk}")

            time_format = "%H:%M"
            booking_time_datetime = datetime.datetime.strptime(booking_time, time_format)
            current_time_datetime = datetime.datetime.strptime(current_time, time_format)
            time_diff = booking_time_datetime - current_time_datetime

            if f"{current_date}" == f"{booking_date}" and time_diff < timedelta(hours=2):
                recipient = User.objects.get(id=request_user_id)
                sender = User.objects.filter(id=1).first() or User.objects.filter(is_superuser=True).first()
                if sender:
                    message = f"{booking_date} {booking_time}의 예약을 {current_date} {current_time}에 취소하셨네요. 가능하면 하루 전에, 늦어도 2시간 전에는 꼭 취소해 주시길 당부드립니다."
                    Note.objects.create(sender=sender, recipient=recipient, message=message)

            new_booking = Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status)
            new_booking.save()
            logger.info(f"새로운 '예약가능' 객체 생성 완료 - 예약ID: {new_booking.pk}, user: {new_booking.user}, 상태: {new_booking.booking_status}")

        send_discord_message_both(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 취소하셨습니다.")
        
        # hidden input으로 전달된 redirect_to 값을 확인하여 리디렉션 결정
        redirect_to = request.POST.get('redirect_to', 'detail')
        if redirect_to == 'create':
            # 예약하기 페이지로 리다이렉트 시 성공 메시지와 캐시 방지를 위해 타임스탬프 추가
            messages.success(request, f'{booking_date} {booking_time} 예약이 성공적으로 취소되었습니다. 해당 시간대를 다시 예약할 수 있습니다.')
            import time
            return redirect(f"{reverse('bookingapp:create')}?refresh={int(time.time())}")
        else:
            messages.success(request, f'{booking_date} {booking_time} 예약이 취소되었습니다.')
            return redirect(reverse('bookingapp:detail', kwargs={'pk': booking.user.pk}))
    return render(request, 'bookingapp/delete.html', {'booking' : booking})
