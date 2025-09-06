import datetime
from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
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
from superapp.utils import is_booking_blocked, send_discord_message_both


def delete_approval_messages(user, booking_date, booking_time):
    """예약 취소/변경 시 기존 승인 메시지를 삭제하는 공통 함수"""
    if user and user.profile:
        approval_message_pattern = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 승인되었습니다."
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


@login_required
def booking(request):
    today_1 = datetime.datetime.today()
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
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        user = request.user
        booking_status = '예약요청'
        # 요청한 날짜가 속한 주의 일요일~토요일 범위 계산
        booking_date_obj = datetime.datetime.strptime(booking_date, '%Y-%m-%d').date()
        # 일요일을 기준으로 주 시작 계산 (일요일=0, 월요일=1, ..., 토요일=6)
        days_since_sunday = (booking_date_obj.weekday() + 1) % 7
        week_start = booking_date_obj - timedelta(days=days_since_sunday)  # 해당 주 일요일
        week_end = week_start + timedelta(days=6)  # 해당 주 토요일
        start_date = week_start
        end_date = week_end
        try:
            request_real_name = request.user.profile.real_name
        except:
            return redirect(reverse('profileapp:create'))
            # return redirect(reverse('accountapp:detail', kwargs={'pk': request.user.pk}))

        # 디버깅: 주1회 예약 제한 체크 (첫 번째 예약 로직)
        weekly_bookings = Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청'))
        logger.info(f"주1회 예약 체크 (첫 번째) - 사용자: {user.username}(ID:{user.id}), 주간범위: {start_date} ~ {end_date}, 기존 예약 수: {weekly_bookings.count()}")
        for wb in weekly_bookings:
            logger.info(f"  기존 예약: ID={wb.pk}, 날짜={wb.booking_date}, 시간={wb.booking_time}, 상태={wb.booking_status}")
        
        if weekly_bookings.count() < 1:
            # 예약 차단 확인 로직 추가
            if is_booking_blocked(booking_date, booking_time):
                logger.info(f"예약 차단됨 - 날짜/시간: {booking_date} {booking_time}")
                errors.append('현재 병원에서 다른 환자의 예약이 진행 중이어서 요청하신 시간의 온라인 예약이 불가능합니다. 잠시 후 다시 시도해 주십시오.')
                return render(request, 'bookingapp/post_write.html', {'errors': errors})
            
            selected_booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
            logger.info(f"선택된 시간대 예약 상태 - 예약ID: {selected_booking.pk}, 상태: {selected_booking.booking_status}, user: {selected_booking.user}")
            
            if selected_booking.booking_status == '예약가능':
                selected_booking.delete()
                new_booking = Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status)
                new_booking.save()
                logger.info(f"예약 성공 - 새 예약ID: {new_booking.pk}, 사용자: {user.username}, 날짜/시간: {booking_date} {booking_time}")
                send_discord_message_both(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
                return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
            else:
                logger.info(f"예약 실패 - 다른 사용자가 먼저 예약함. 선택된 예약 상태: {selected_booking.booking_status}")
                errors.append('안타깝게도 예약하시는 사이 다른 분이 먼저 예약요청 버튼을 누르셨습니다. 다른 시간대를 선택해서 예약요청해 주세요.')
                return render(request, 'bookingapp/post_write.html', {'errors': errors})
        else:
            logger.info(f"주1회 예약 제한 - 사용자: {user.username}, 이미 {weekly_bookings.count()}개의 예약 존재")
            errors.append('온라인 예약은 주 1회만 가능합니다.')
            return render(request, 'bookingapp/post_write.html', {'errors': errors})
    return render(request, 'bookingapp/create.html', context)


@login_required
def booking_2(request):
    today_1 = datetime.datetime.today()
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
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        user = request.user
        booking_status = '예약요청'
        # 요청한 날짜가 속한 주의 일요일~토요일 범위 계산
        booking_date_obj = datetime.datetime.strptime(booking_date, '%Y-%m-%d').date()
        # 일요일을 기준으로 주 시작 계산 (일요일=0, 월요일=1, ..., 토요일=6)
        days_since_sunday = (booking_date_obj.weekday() + 1) % 7
        week_start = booking_date_obj - timedelta(days=days_since_sunday)  # 해당 주 일요일
        week_end = week_start + timedelta(days=6)  # 해당 주 토요일
        start_date = week_start
        end_date = week_end
        try:
            request_real_name = request.user.profile.real_name
        except:
            return redirect(reverse('profileapp:create'))
            # return redirect(reverse('accountapp:detail', kwargs={'pk': request.user.pk}))

        # 디버깅: 주1회 예약 제한 체크 (두 번째 예약 로직)
        weekly_bookings_2 = Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청'))
        logger.info(f"주1회 예약 체크 (두 번째) - 사용자: {user.username}(ID:{user.id}), 주간범위: {start_date} ~ {end_date}, 기존 예약 수: {weekly_bookings_2.count()}")
        for wb in weekly_bookings_2:
            logger.info(f"  기존 예약: ID={wb.pk}, 날짜={wb.booking_date}, 시간={wb.booking_time}, 상태={wb.booking_status}")

        if weekly_bookings_2.count() < 1:
            # 예약 차단 확인 로직 추가
            if is_booking_blocked(booking_date, booking_time):
                logger.info(f"예약 차단됨 (두 번째) - 날짜/시간: {booking_date} {booking_time}")
                errors.append('현재 병원에서 다른 환자의 예약이 진행 중이어서 요청하신 시간의 온라인 예약이 불가능합니다. 잠시 후 다시 시도해 주십시오.')
                return render(request, 'bookingapp/post_write.html', {'errors': errors})
            
            selected_booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
            logger.info(f"선택된 시간대 예약 상태 (두 번째) - 예약ID: {selected_booking.pk}, 상태: {selected_booking.booking_status}, user: {selected_booking.user}")
            
            if selected_booking.booking_status == '예약가능':
                selected_booking.delete()
                new_booking = Booking(booking_date=booking_date, booking_time=booking_time, user=user,
                        booking_status=booking_status)
                new_booking.save()
                logger.info(f"예약 성공 (두 번째) - 새 예약ID: {new_booking.pk}, 사용자: {user.username}, 날짜/시간: {booking_date} {booking_time}")
                send_discord_message_both(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
                return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
            else:
                logger.info(f"예약 실패 (두 번째) - 다른 사용자가 먼저 예약함. 선택된 예약 상태: {selected_booking.booking_status}")
                errors.append('예약하시는 동안 다른 분이 먼저 예약요청 버튼을 누르셨습니다. 다른 시간대를 선택해서 예약요청해 주세요.')
                return render(request, 'bookingapp/post_write.html', {'errors': errors})
        else:
            logger.info(f"주1회 예약 제한 (두 번째) - 사용자: {user.username}, 이미 {weekly_bookings_2.count()}개의 예약 존재")
            errors.append('온라인 예약은 주 1회만 가능합니다.')
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
    booking = Booking.objects.get(pk=pk)
    booking_date = booking.booking_date
    booking_time = booking.booking_time
    user = ''
    booking_status = '예약가능'
    request_real_name = booking.user.profile.real_name
    request_user_id = booking.user_id
    if request.method == 'POST':
        # 디버깅: 예약 취소 전 상태 로깅
        logger.info(f"예약 취소 시작 - 사용자: {request_real_name}(ID:{request_user_id}), 예약ID: {booking.pk}, 날짜/시간: {booking_date} {booking_time}, 상태: {booking.booking_status}")
        
        # 예약 취소 시 기존 승인 메시지 삭제
        delete_approval_messages(booking.user, booking_date, booking_time)
        
        booking.delete()
        logger.info(f"기존 예약 삭제 완료 - 예약ID: {booking.pk}")
        
        send_discord_message_both(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 취소하셨습니다.")

        time_format = "%H:%M"
        booking_time_datetime = datetime.datetime.strptime(booking_time, time_format)
        current_time_datetime = datetime.datetime.strptime(current_time, time_format)
        time_diff = booking_time_datetime - current_time_datetime

        if f"{current_date}" == f"{booking_date}" and time_diff < timedelta(hours=2):
            recipient_id = request_user_id
            message = f"{booking_date} {booking_time}의 예약을 {current_date} {current_time}에 취소하셨네요. 가능하면 하루 전에, 늦어도 2시간 전에는 꼭 취소해 주시길 당부드립니다."
            recipient = User.objects.get(id=recipient_id)
            # recipient = User.objects.get(id=28)
            sender = User.objects.get(id=1)
            note = Note.objects.create(sender=sender, recipient=recipient, message=message)

        # 새로운 '예약가능' 상태 객체 생성
        new_booking = Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status)
        new_booking.save()
        logger.info(f"새로운 '예약가능' 객체 생성 완료 - 예약ID: {new_booking.pk}, user: {new_booking.user}, 상태: {new_booking.booking_status}")
        
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
