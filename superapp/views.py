import datetime
from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, DeleteView

from bookingapp.decorators import booking_ownership_required
from bookingapp.models import Booking, BOOKING_TIME
from profileapp.utils import is_tablet_user
from superapp.utils import send_discord_message
from articleapp.models import WaitingOverride, WaitingPatient
from articleapp.waiting_utils import (
    MAX_WAITING,
    current_waiting_period,
    period_label,
    sync_waiting_count,
    waiting_board,
    waiting_count,
    waiting_gate,
)
import requests
from noteapp.models import Note
import os, environ
from pathlib import Path
from django.contrib import messages


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


env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(
    env_file=os.path.join(BASE_DIR, '.env')
)

# Create your views here.
has_ownership = [
    login_required, booking_ownership_required
]


def aligo_sms_send(rec, msg_2):
    send_url = 'https://apis.aligo.in/send/'  # 요청을 던지는 URL, 현재는 문자보내기
    sms_data = {'key': env('ALIGO_KEY'),
                'userid': 'prpc8575',  # 알리고 사이트 아이디
                'sender': '053-801-8575',  # 발신번호
                'receiver': rec,  # 수신번호 (,활용하여 1000명까지 추가 가능)
                'msg': msg_2,  # 문자 내용
                'msg_type': 'sms',  # 메세지 타입 (SMS, LMS)
                }
    send_response = requests.post(send_url, data=sms_data)
    print(send_response.json())


@login_required
def superbooking(request):
    today_1 = datetime.datetime.today()
    today_2 = today_1 + timedelta(days=1)
    today_3 = today_1 + timedelta(days=2)
    today_4 = today_1 + timedelta(days=3)
    today_5 = today_1 + timedelta(days=4)
    today_6 = today_1 + timedelta(days=5)
    today_7 = today_1 + timedelta(days=6)

    inform_today_1 = Booking.objects.filter(booking_date=today_1.strftime('%Y-%m-%d'))
    inform_today_2 = Booking.objects.filter(booking_date=today_2.strftime('%Y-%m-%d'))
    inform_today_3 = Booking.objects.filter(booking_date=today_3.strftime('%Y-%m-%d'))
    inform_today_4 = Booking.objects.filter(booking_date=today_4.strftime('%Y-%m-%d'))
    inform_today_5 = Booking.objects.filter(booking_date=today_5.strftime('%Y-%m-%d'))
    inform_today_6 = Booking.objects.filter(booking_date=today_6.strftime('%Y-%m-%d'))
    inform_today_7 = Booking.objects.filter(booking_date=today_7.strftime('%Y-%m-%d'))

    context = {'inform_today_1': inform_today_1,
               'inform_today_2': inform_today_2,
               'inform_today_3': inform_today_3,
               'inform_today_4': inform_today_4,
               'inform_today_5': inform_today_5,
               'inform_today_6': inform_today_6,
               'inform_today_7': inform_today_7,
               }

    if request.user.is_superuser:
        # 차단 상태 정보 추가
        from .utils import get_block_status, get_blocked_slots
        block_status = get_block_status()
        blocked_slots = get_blocked_slots()
        
        context.update({
            'block_status': block_status,
            'blocked_slots': blocked_slots,
            'is_blocking_active': block_status is not None,
        })

        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            booking_user_id = request.POST.get('booking_user_id')
            try:
                pre_booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
            except:
                pre_booking = None

            user = None
            if booking_status == '예약요청':
                if booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user,
                            booking_rn=booking_rn).save()
                else:
                    return HttpResponse("예약요청자를 선택하지 않으셨습니다.")
            elif booking_status == '예약승인':
                if pre_booking and pre_booking.user is not None:
                    user = pre_booking.user
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time,
                                      booking_status=booking_status,
                                      user=user, booking_rn=booking_rn).save()
                    recipient_id = user.id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user, booking_rn=booking_rn).save()
                    recipient_id = booking_user_id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif not booking_rn and not booking_user_id:
                    return HttpResponse("예약승인자를 선택하지 않으셨습니다.")
                elif booking_rn and not booking_user_id:
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            booking_rn=booking_rn).save()
            elif booking_status == '예약가능':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    # 예약 취소 시 승인 메시지 삭제
                    existing_booking = booking.first()
                    if existing_booking and existing_booking.user:
                        delete_approval_messages(existing_booking.user, booking_date, booking_time)
                    booking.delete()
                Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
            elif booking_status == '예약불가':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    booking.delete()
            return redirect(reverse('superapp:supercreate'))
        return render(request, 'superapp/supercreate.html', context)
    else:
        return redirect(reverse('articleapp:index'))


@login_required
def superbooking2(request):
    today_1 = datetime.datetime.today()
    today_8 = today_1 + timedelta(days=7)
    today_9 = today_1 + timedelta(days=8)
    today_10 = today_1 + timedelta(days=9)
    today_11 = today_1 + timedelta(days=10)
    today_12 = today_1 + timedelta(days=11)
    today_13 = today_1 + timedelta(days=12)
    today_14 = today_1 + timedelta(days=13)
    today_15 = today_1 + timedelta(days=14)
    inform_today_8 = Booking.objects.filter(booking_date = today_8.strftime('%Y-%m-%d'))
    inform_today_9 = Booking.objects.filter(booking_date = today_9.strftime('%Y-%m-%d'))
    inform_today_10 = Booking.objects.filter(booking_date = today_10.strftime('%Y-%m-%d'))
    inform_today_11 = Booking.objects.filter(booking_date = today_11.strftime('%Y-%m-%d'))
    inform_today_12 = Booking.objects.filter(booking_date = today_12.strftime('%Y-%m-%d'))
    inform_today_13 = Booking.objects.filter(booking_date = today_13.strftime('%Y-%m-%d'))
    inform_today_14 = Booking.objects.filter(booking_date = today_14.strftime('%Y-%m-%d'))
    inform_today_15 = Booking.objects.filter(booking_date = today_15.strftime('%Y-%m-%d'))

    context = {'inform_today_8': inform_today_8,
               'inform_today_9': inform_today_9,
               'inform_today_10': inform_today_10,
               'inform_today_11': inform_today_11,
               'inform_today_12': inform_today_12,
               'inform_today_13': inform_today_13,
               'inform_today_14': inform_today_14,
               'inform_today_15': inform_today_15,
               }
    if request.user.is_superuser:
        # 차단 상태 정보 추가
        from .utils import get_block_status, get_blocked_slots
        block_status = get_block_status()
        blocked_slots = get_blocked_slots()
        
        context.update({
            'block_status': block_status,
            'blocked_slots': blocked_slots,
            'is_blocking_active': block_status is not None,
        })

        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            booking_user_id = request.POST.get('booking_user_id')
            try:
                pre_booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
            except:
                pre_booking = None

            user = None
            if booking_status == '예약요청':
                if booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user,
                            booking_rn=booking_rn).save()
                else:
                    return HttpResponse("예약요청자를 선택하지 않으셨습니다.")
            elif booking_status == '예약승인':
                if pre_booking and pre_booking.user is not None:
                    user = pre_booking.user
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time,
                                      booking_status=booking_status,
                                      user=user, booking_rn=booking_rn).save()
                    recipient_id = user.id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user, booking_rn=booking_rn).save()
                    recipient_id = booking_user_id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif not booking_rn and not booking_user_id:
                    return HttpResponse("예약승인자를 선택하지 않으셨습니다.")
                elif booking_rn and not booking_user_id:
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            booking_rn=booking_rn).save()
            elif booking_status == '예약가능':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    # 예약 취소 시 승인 메시지 삭제
                    existing_booking = booking.first()
                    if existing_booking and existing_booking.user:
                        delete_approval_messages(existing_booking.user, booking_date, booking_time)
                    booking.delete()
                Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
            elif booking_status == '예약불가':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    booking.delete()
            return redirect(reverse('superapp:supercreate2'))
        return render(request, 'superapp/supercreate2.html', context)
    else:
        return redirect(reverse('articleapp:index'))


@login_required
def superbooking2_1(request):
    today_1 = datetime.datetime.today()
    today_16 = today_1 + timedelta(days=15)
    today_17 = today_1 + timedelta(days=16)
    today_18 = today_1 + timedelta(days=17)
    today_19 = today_1 + timedelta(days=18)
    today_20 = today_1 + timedelta(days=19)
    today_21 = today_1 + timedelta(days=20)
    today_22 = today_1 + timedelta(days=21)
    today_23 = today_1 + timedelta(days=22)
    inform_today_16 = Booking.objects.filter(booking_date = today_16.strftime('%Y-%m-%d'))
    inform_today_17 = Booking.objects.filter(booking_date = today_17.strftime('%Y-%m-%d'))
    inform_today_18 = Booking.objects.filter(booking_date = today_18.strftime('%Y-%m-%d'))
    inform_today_19 = Booking.objects.filter(booking_date = today_19.strftime('%Y-%m-%d'))
    inform_today_20 = Booking.objects.filter(booking_date = today_20.strftime('%Y-%m-%d'))
    inform_today_21 = Booking.objects.filter(booking_date = today_21.strftime('%Y-%m-%d'))
    inform_today_22 = Booking.objects.filter(booking_date = today_22.strftime('%Y-%m-%d'))
    inform_today_23 = Booking.objects.filter(booking_date = today_23.strftime('%Y-%m-%d'))

    context = {'inform_today_16': inform_today_16,
               'inform_today_17': inform_today_17,
               'inform_today_18': inform_today_18,
               'inform_today_19': inform_today_19,
               'inform_today_20': inform_today_20,
               'inform_today_21': inform_today_21,
               'inform_today_22': inform_today_22,
               'inform_today_23': inform_today_23,
               }
    if request.user.is_superuser:
        # 차단 상태 정보 추가
        from .utils import get_block_status, get_blocked_slots
        block_status = get_block_status()
        blocked_slots = get_blocked_slots()
        
        context.update({
            'block_status': block_status,
            'blocked_slots': blocked_slots,
            'is_blocking_active': block_status is not None,
        })

        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            booking_user_id = request.POST.get('booking_user_id')
            try:
                pre_booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
            except:
                pre_booking = None

            user = None
            if booking_status == '예약요청':
                if booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user,
                            booking_rn=booking_rn).save()
                else:
                    return HttpResponse("예약요청자를 선택하지 않으셨습니다.")
            elif booking_status == '예약승인':
                if pre_booking and pre_booking.user is not None:
                    user = pre_booking.user
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time,
                                      booking_status=booking_status,
                                      user=user, booking_rn=booking_rn).save()
                    recipient_id = user.id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user, booking_rn=booking_rn).save()
                    recipient_id = booking_user_id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif not booking_rn and not booking_user_id:
                    return HttpResponse("예약승인자를 선택하지 않으셨습니다.")
                elif booking_rn and not booking_user_id:
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            booking_rn=booking_rn).save()
            elif booking_status == '예약가능':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    # 예약 취소 시 승인 메시지 삭제
                    existing_booking = booking.first()
                    if existing_booking and existing_booking.user:
                        delete_approval_messages(existing_booking.user, booking_date, booking_time)
                    booking.delete()
                Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
            elif booking_status == '예약불가':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    booking.delete()
            return redirect(reverse('superapp:supercreate2_1'))
        return render(request, 'superapp/supercreate2_1.html', context)
    else:
        return redirect(reverse('articleapp:index'))


@login_required
def superbooking2_2(request):
    today_1 = datetime.datetime.today()
    today_24 = today_1 + timedelta(days=23)
    today_25 = today_1 + timedelta(days=24)
    today_26 = today_1 + timedelta(days=25)
    today_27 = today_1 + timedelta(days=26)
    today_28 = today_1 + timedelta(days=27)
    today_29 = today_1 + timedelta(days=28)
    today_30 = today_1 + timedelta(days=29)
    today_31 = today_1 + timedelta(days=30)
    inform_today_24 = Booking.objects.filter(booking_date = today_24.strftime('%Y-%m-%d'))
    inform_today_25 = Booking.objects.filter(booking_date = today_25.strftime('%Y-%m-%d'))
    inform_today_26 = Booking.objects.filter(booking_date = today_26.strftime('%Y-%m-%d'))
    inform_today_27 = Booking.objects.filter(booking_date = today_27.strftime('%Y-%m-%d'))
    inform_today_28 = Booking.objects.filter(booking_date = today_28.strftime('%Y-%m-%d'))
    inform_today_29 = Booking.objects.filter(booking_date = today_29.strftime('%Y-%m-%d'))
    inform_today_30 = Booking.objects.filter(booking_date = today_30.strftime('%Y-%m-%d'))
    inform_today_31 = Booking.objects.filter(booking_date = today_31.strftime('%Y-%m-%d'))

    context = {'inform_today_24': inform_today_24,
               'inform_today_25': inform_today_25,
               'inform_today_26': inform_today_26,
               'inform_today_27': inform_today_27,
               'inform_today_28': inform_today_28,
               'inform_today_29': inform_today_29,
               'inform_today_30': inform_today_30,
               'inform_today_31': inform_today_31,
               }
    if request.user.is_superuser:
        # 차단 상태 정보 추가
        from .utils import get_block_status, get_blocked_slots
        block_status = get_block_status()
        blocked_slots = get_blocked_slots()
        
        context.update({
            'block_status': block_status,
            'blocked_slots': blocked_slots,
            'is_blocking_active': block_status is not None,
        })

        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            booking_user_id = request.POST.get('booking_user_id')
            try:
                pre_booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
            except:
                pre_booking = None

            user = None
            if booking_status == '예약요청':
                if booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user,
                            booking_rn=booking_rn).save()
                else:
                    return HttpResponse("예약요청자를 선택하지 않으셨습니다.")
            elif booking_status == '예약승인':
                if pre_booking and pre_booking.user is not None:
                    user = pre_booking.user
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time,
                                      booking_status=booking_status,
                                      user=user, booking_rn=booking_rn).save()
                    recipient_id = user.id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif booking_user_id:
                    try:
                        user = User.objects.get(id=booking_user_id)
                    except User.DoesNotExist:
                        return HttpResponse("그런 ID는 없습니다.")
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            user=user, booking_rn=booking_rn).save()
                    recipient_id = booking_user_id
                    message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 확정되었습니다."
                    recipient = User.objects.get(id=recipient_id)
                    sender = request.user
                    Note.objects.create(sender=sender, recipient=recipient, message=message)
                elif not booking_rn and not booking_user_id:
                    return HttpResponse("예약승인자를 선택하지 않으셨습니다.")
                elif booking_rn and not booking_user_id:
                    booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                    if booking.exists():
                        booking.delete()
                    Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status,
                            booking_rn=booking_rn).save()
            elif booking_status == '예약가능':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    # 예약 취소 시 승인 메시지 삭제
                    existing_booking = booking.first()
                    if existing_booking and existing_booking.user:
                        delete_approval_messages(existing_booking.user, booking_date, booking_time)
                    booking.delete()
                Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
            elif booking_status == '예약불가':
                booking = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time)
                if booking.exists():
                    booking.delete()
            return redirect(reverse('superapp:supercreate2_2'))
        return render(request, 'superapp/supercreate2_2.html', context)
    else:
        return redirect(reverse('articleapp:index'))


@login_required
def superbooking3(request):
    if request.user.is_superuser:
        dict_book = Booking.objects.filter(user__isnull=False).order_by('-id')[:120]
        context = {
            'bookings': dict_book
        }
        if request.method == 'POST':
            rec = request.POST.get('rec')
            msg = request.POST.get('msg')
            name = request.POST.get('name')
            date = request.POST.get('date')
            time = request.POST.get('time')
            if str(msg)=='ok':
                msg_2 = f"{name}님, {date} {time}분의 예약이 확정되었습니다."
                aligo_sms_send(rec, msg_2)
            elif str(msg)=='cancel':
                msg_2 = f"{name}님, {date} {time}분의 예약이 취소되었습니다."
                aligo_sms_send(rec, msg_2)
        return render(request, 'superapp/supercreate3.html', context)
    elif not request.user.is_superuser:
        return redirect(reverse('articleapp:index'))


@login_required
def superbooking4(request):
    if request.user.is_superuser:
        dict_book = Booking.objects.filter(user__isnull=True).order_by('-id')[:120]
        context = {
            'bookings': dict_book
        }
        if request.method == 'POST':
            rec = request.POST.get('rec')
            msg = request.POST.get('msg')
            name = request.POST.get('name')
            date = request.POST.get('date')
            time = request.POST.get('time')
            if str(msg)=='ok':
                msg_2 = f"{name}님, {date} {time}분의 예약이 확정되었습니다."
                aligo_sms_send(rec, msg_2)
            elif str(msg)=='cancel':
                msg_2 = f"{name}님, {date} {time}분의 예약이 취소되었습니다."
                aligo_sms_send(rec, msg_2)
        return render(request, 'superapp/supercreate4.html', context)
    elif not request.user.is_superuser:
        return redirect(reverse('articleapp:index'))


@login_required
def block_online_bookings(request):
    """
    온라인 예약을 일괄 차단하는 뷰 함수
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("슈퍼유저만 접근 가능합니다.")
    
    if request.method == 'POST':
        from .utils import block_all_available_bookings
        
        try:
            result = block_all_available_bookings(user_id=request.user.id)
            
            if result['success'] > 0:
                messages.success(
                    request, 
                    f"온라인 예약이 일괄 차단되었습니다. "
                    f"총 {result['total']}개 시간대 중 {result['success']}개 차단 완료"
                    + (f", {result['failed']}개 실패" if result['failed'] > 0 else "")
                )
            else:
                messages.error(request, "예약 차단에 실패했습니다.")
                
        except Exception as e:
            messages.error(request, f"예약 차단 중 오류가 발생했습니다: {str(e)}")
    
    # 요청이 온 페이지로 리다이렉트
    referer = request.META.get('HTTP_REFERER')
    if referer and 'supercreate' in referer:
        if 'supercreate2' in referer:
            return redirect(reverse('superapp:supercreate2'))
        elif 'supercreate2_1' in referer:
            return redirect(reverse('superapp:supercreate2_1'))
        elif 'supercreate3' in referer:
            return redirect(reverse('superapp:supercreate3'))
        elif 'supercreate4' in referer:
            return redirect(reverse('superapp:supercreate4'))
        else:
            return redirect(reverse('superapp:supercreate'))
    
    return redirect(reverse('superapp:supercreate'))


@login_required
def unblock_online_bookings(request):
    """
    온라인 예약 차단을 수동으로 해제하는 뷰 함수
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("슈퍼유저만 접근 가능합니다.")
    
    if request.method == 'POST':
        from .utils import unblock_all_bookings
        
        try:
            success = unblock_all_bookings()
            
            if success:
                messages.success(request, "온라인 예약 차단이 해제되었습니다.")
            else:
                messages.error(request, "예약 차단 해제에 실패했습니다.")
                
        except Exception as e:
            messages.error(request, f"예약 차단 해제 중 오류가 발생했습니다: {str(e)}")
    
    # 요청이 온 페이지로 리다이렉트
    referer = request.META.get('HTTP_REFERER')
    if referer and 'supercreate' in referer:
        if 'supercreate2' in referer:
            return redirect(reverse('superapp:supercreate2'))
        elif 'supercreate2_1' in referer:
            return redirect(reverse('superapp:supercreate2_1'))
        elif 'supercreate3' in referer:
            return redirect(reverse('superapp:supercreate3'))
        elif 'supercreate4' in referer:
            return redirect(reverse('superapp:supercreate4'))
        else:
            return redirect(reverse('superapp:supercreate'))
    
    return redirect(reverse('superapp:supercreate'))


# @method_decorator(login_required, 'get')
# @method_decorator(login_required, 'post')
# class BookingDetailView(DetailView):
#     model = Booking
#     context_object_name = 'user'
#     template_name = 'bookingapp/detail.html'
#     def get_object(self):
#         return self.request.user
#     def get(self, *args, **kwargs):
#         if self.request.user.is_authenticated and self.get_object() == self.request.user:
#             return super().get(*args, **kwargs)
#         else:
#             return HttpResponseForbidden()
#     def post(self, *args, **kwargs):
#         if self.request.user.is_authenticated and self.get_object() == self.request.user:
#             return super().post(*args, **kwargs)
#         else:
#             return HttpResponseForbidden()
#
#
# @method_decorator(has_ownership, 'get')
# @method_decorator(has_ownership, 'post')
# class BookingDeleteView(DeleteView):
#     model = Booking
#     context_object_name = 'booking'
#     success_url = reverse_lazy('bookingapp:create')
#     template_name = 'bookingapp/delete.html'
#
# @login_required
# @booking_ownership_required
# def booking_delete(request, pk):
#     booking = Booking.objects.get(pk=pk)
#     booking_date = booking.booking_date
#     booking_time = booking.booking_time
#     user = ''
#     booking_status = '예약가능'
#     request_real_name = booking.user.profile.real_name
#     old_booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
#     if request.method == 'POST':
#         booking.delete()
#         old_booking.delete()
#         Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
#         return redirect(reverse('bookingapp:detail', kwargs={'pk': booking.user.pk}))
#     return render(request, 'bookingapp/delete.html', {'booking' : booking})


TABLET_HIDDEN_TIMES = {'10:20', '11:05', '11:50', '15:20', '16:05', '16:50', '19:05', '19:50'}


def tablet_time_kind(weekday, time_value):
    if time_value in TABLET_HIDDEN_TIMES:
        return None
    if weekday == 6:
        return None
    if weekday == 5:
        if '09:20' <= time_value <= '12:30':
            return 'slot'
        return None
    if weekday == 2:
        if '14:20' <= time_value <= '20:05':
            return 'slot'
        return None
    if time_value == '13:00':
        return 'lunch'
    if '09:20' <= time_value <= '17:30':
        return 'slot'
    return None


def _tablet_page(request, days, page_url_name):
    if not is_tablet_user(request.user) and not request.user.is_superuser:
        return redirect('articleapp:index')

    target_date = datetime.date.today() + timedelta(days=days)
    target_date_str = target_date.strftime('%Y-%m-%d')
    weekday_names = ['월', '화', '수', '목', '금', '토', '일']

    if request.method == 'POST':
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        if booking_date != target_date_str:
            messages.error(request, '선택할 수 있는 날짜가 아닙니다.')
        elif tablet_time_kind(target_date.weekday(), booking_time) != 'slot':
            messages.error(request, '선택할 수 없는 시간입니다. 다른 시간을 선택해 주세요.')
        elif Booking.objects.filter(booking_status='선택중').exists():
            messages.error(request, '이미 선택된 시간이 있습니다. 직원이 처리한 뒤 다시 선택해 주세요.')
        else:
            slot = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
            if slot is None or slot.booking_status != '예약가능':
                messages.error(request, '선택할 수 없는 시간입니다. 다른 시간을 선택해 주세요.')
            else:
                slot.delete()
                Booking(booking_date=booking_date, booking_time=booking_time, booking_status='선택중').save()
                request.session['tablet_selected'] = {'date': booking_date, 'time': booking_time}
        return redirect(page_url_name)

    time_rows = []
    weekday = target_date.weekday()
    for time_value, label in BOOKING_TIME:
        kind = tablet_time_kind(weekday, time_value)
        if kind is None:
            continue
        time_rows.append({
            'time': time_value,
            'label': '점심시간' if time_value == '13:00' else time_value,
            'kind': kind,
        })

    inform_today = Booking.objects.filter(booking_date=target_date_str)
    waiting_slot = Booking.objects.filter(booking_status='선택중').first()
    context = {
        'inform_today': inform_today,
        'target_date': target_date_str,
        'target_weekday': weekday_names[target_date.weekday()],
        'time_rows': time_rows,
        'has_selection': waiting_slot is not None,
        'selected_date': waiting_slot.booking_date.strftime('%Y-%m-%d') if waiting_slot else '',
        'selected_time': waiting_slot.booking_time if waiting_slot else '',
        'tablet_page_url': reverse(page_url_name),
        'tablet_days': days,
    }
    return render(request, 'superapp/tablet.html', context)


@login_required
def tablet_booking(request):
    return _tablet_page(request, 14, 'superapp:tablet')


@login_required
def tablet_booking2(request):
    return _tablet_page(request, 21, 'superapp:tablet2')


@login_required
def tablet_booking3(request):
    return _tablet_page(request, 28, 'superapp:tablet3')


@login_required
def tablet_status(request):
    if not is_tablet_user(request.user) and not request.user.is_superuser:
        return JsonResponse({'state': 'forbidden'}, status=403)
    booking_date = request.GET.get('date')
    booking_time = request.GET.get('time')
    if booking_date and booking_time:
        slot = Booking.objects.filter(booking_date=booking_date, booking_time=booking_time).first()
        if slot is None:
            return JsonResponse({'state': 'cleared'})
        if slot.booking_status == '선택중':
            return JsonResponse({'state': 'waiting'})
        if slot.booking_status == '예약승인':
            return JsonResponse({'state': 'approved'})
        return JsonResponse({'state': 'cleared'})
    if Booking.objects.filter(booking_status='선택중').exists():
        return JsonResponse({'state': 'waiting'})
    return JsonResponse({'state': 'idle'})


@login_required
def tablet_slots(request):
    if not is_tablet_user(request.user) and not request.user.is_superuser:
        return JsonResponse({}, status=403)
    try:
        days = int(request.GET.get('days', 14))
    except (TypeError, ValueError):
        days = 14
    if days not in (14, 21, 28):
        days = 14
    target_date = datetime.date.today() + timedelta(days=days)
    bookings = Booking.objects.filter(booking_date=target_date)
    return JsonResponse({
        'date': target_date.strftime('%Y-%m-%d'),
        'slots': {item.booking_time: item.booking_status for item in bookings},
    })


@login_required
def tablet_pending(request):
    if not request.user.is_superuser:
        return JsonResponse({'slots': []}, status=403)
    slots = Booking.objects.filter(booking_status='선택중').values('booking_date', 'booking_time')
    return JsonResponse({
        'slots': [
            {'date': item['booking_date'].strftime('%Y-%m-%d'), 'time': item['booking_time']}
            for item in slots
        ]
    })


def _tablet_waiting_allowed(user):
    return is_tablet_user(user) or user.is_superuser


@login_required
def waiting_pt(request):
    if not _tablet_waiting_allowed(request.user):
        return redirect('articleapp:index')

    today = datetime.date.today()
    gate = waiting_gate()
    period = gate['period']
    count = 0
    if period:
        count = sync_waiting_count(today, period)

    if request.method == 'POST':
        if not gate['can_input']:
            messages.error(request, gate['message'].replace('\n', ' '))
            return redirect('superapp:waiting_pt')
        if count >= MAX_WAITING:
            return redirect('superapp:waiting_pt')
        real_name = (request.POST.get('real_name') or '').strip()
        birth_date = (request.POST.get('birth_date') or '').strip()
        if len(real_name) < 2:
            messages.error(request, '이름을 입력해 주세요.')
            return redirect('superapp:waiting_pt')
        if len(birth_date) != 8 or not birth_date.isdigit():
            messages.error(request, '생년월일 8자리를 입력해 주세요.')
            return redirect('superapp:waiting_pt')
        year = int(birth_date[:4])
        if year < 1910 or year > datetime.date.today().year:
            messages.error(request, '생년월일을 다시 확인해 주세요.')
            return redirect('superapp:waiting_pt')
        exists = WaitingPatient.objects.filter(
            visit_date=today,
            period=period,
            real_name=real_name,
            birth_date=birth_date,
        ).exists()
        if exists:
            messages.error(request, '이미 접수되었습니다.')
            return redirect('superapp:waiting_pt')
        WaitingPatient.objects.create(
            real_name=real_name,
            birth_date=birth_date,
            visit_date=today,
            period=period,
        )
        count = sync_waiting_count(today, period)
        send_discord_message(f"선착순 대기 환자수 : {count}명")
        return redirect(reverse('superapp:waiting_pt') + '?done=' + str(count))

    context = {
        'period': period,
        'period_label': period_label(period),
        'count': count,
        'max_waiting': MAX_WAITING,
        'closed': bool(period and count >= MAX_WAITING),
        'can_input': bool(gate['can_input'] and count < MAX_WAITING),
        'gate_message': gate['message'],
        'done': request.GET.get('done'),
        'board': waiting_board(today, period) if period else [],
    }
    return render(request, 'superapp/waiting_pt.html', context)


@login_required
def waiting_pt_status(request):
    if not _tablet_waiting_allowed(request.user):
        return JsonResponse({}, status=403)
    today = datetime.date.today()
    gate = waiting_gate()
    period = gate['period']
    count = waiting_count(today, period) if period else 0
    return JsonResponse({
        'period': period or '',
        'period_label': period_label(period),
        'count': count,
        'closed': bool(period and count >= MAX_WAITING),
        'can_input': bool(gate['can_input'] and count < MAX_WAITING),
        'message': gate['message'],
        'board': waiting_board(today, period) if period else [],
    })


@login_required
def waiting_list(request):
    if not request.user.is_superuser:
        return redirect('articleapp:index')
    today = datetime.date.today()
    tomorrow = today + timedelta(days=1)
    if request.method == 'POST':
        override_day = request.POST.get('override_day')
        override_mode = request.POST.get('override_mode')
        if override_day in ('today', 'tomorrow') and override_mode in ('open', 'closed', 'clear'):
            target = today if override_day == 'today' else tomorrow
            if override_mode == 'clear':
                WaitingOverride.objects.filter(visit_date=target).delete()
            else:
                WaitingOverride.objects.update_or_create(
                    visit_date=target,
                    defaults={'mode': override_mode},
                )
            return redirect('superapp:waiting_list')
        patient_id = request.POST.get('patient_id')
        patient = WaitingPatient.objects.filter(pk=patient_id, visit_date=today).first()
        if patient:
            period = patient.period
            patient.delete()
            count = sync_waiting_count(today, period)
            send_discord_message(f"선착순 대기 환자수 : {count}명")
        return redirect('superapp:waiting_list')
    patients = WaitingPatient.objects.filter(visit_date=today).order_by('created_at')
    overrides = {
        item.visit_date: item.mode
        for item in WaitingOverride.objects.filter(visit_date__in=[today, tomorrow])
    }
    context = {
        'today': today,
        'tomorrow': tomorrow,
        'am_patients': patients.filter(period='am'),
        'pm_patients': patients.filter(period='pm'),
        'period': current_waiting_period(),
        'period_label': period_label(current_waiting_period()),
        'today_override': overrides.get(today),
        'tomorrow_override': overrides.get(tomorrow),
    }
    return render(request, 'superapp/waiting_list.html', context)


def _waiting_list_payload(today):
    patients = WaitingPatient.objects.filter(visit_date=today).order_by('created_at')
    def rows(period):
        return [
            {
                'id': item.id,
                'name': item.real_name,
                'birth': item.birth_date,
                'time': item.created_at.strftime('%H:%M'),
            }
            for item in patients if item.period == period
        ]
    return {'am': rows('am'), 'pm': rows('pm')}


@login_required
def waiting_list_status(request):
    if not request.user.is_superuser:
        return JsonResponse({}, status=403)
    return JsonResponse(_waiting_list_payload(datetime.date.today()))

