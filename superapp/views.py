import datetime
from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, DeleteView

from bookingapp.decorators import booking_ownership_required
from bookingapp.models import Booking
import requests

from noteapp.models import Note

import os, environ
from pathlib import Path


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
    if request.user.is_superuser:
        errors = []
        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            try:
                booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
                if booking_status == '예약요청':
                    user = booking.user
                    booking.delete()
                elif booking_status == '예약승인':
                    user = booking.user
                    recipient_id = booking.user_id
                    if user:
                        message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 승인되었습니다."
                        recipient = User.objects.get(id=recipient_id)
                        sender = request.user
                        note = Note.objects.create(sender=sender, recipient=recipient, message=message)
                    booking.delete()
                elif booking_status == '예약가능':
                    booking.delete()
                    user = None
                elif booking_status == '예약불가':
                    booking.delete()
                    user = None
            except Booking.DoesNotExist:
                booking = None
                user = None
            booking_date_parse = parse(booking_date)
            booking_date_weekday = booking_date_parse.weekday()
            start_date = booking_date_parse - timedelta(days=booking_date_weekday)
            end_date = booking_date_parse + timedelta(days=(5 - booking_date_weekday))
            request_real_name = request.user.profile.real_name
            if Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청')).count() < 1000:
                Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status, booking_rn=booking_rn).save()
                return redirect(reverse('superapp:supercreate'))
            else:
                errors.append('주 2회 예약이 넘었는지 확인하세요.')
                return render(request, 'superapp/supercreate.html', {'errors': errors})
        return render(request, 'superapp/supercreate.html', context)
    elif not request.user.is_superuser:
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
        errors = []
        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            try:
                booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
                if booking_status == '예약요청':
                    user = booking.user
                    booking.delete()
                elif booking_status == '예약승인':
                    user = booking.user
                    recipient_id = booking.user_id
                    if user:
                        message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 승인되었습니다."
                        recipient = User.objects.get(id=recipient_id)
                        sender = request.user
                        note = Note.objects.create(sender=sender, recipient=recipient, message=message)
                    booking.delete()
                elif booking_status == '예약가능':
                    booking.delete()
                    user = None
                elif booking_status == '예약불가':
                    booking.delete()
                    user = None
            except Booking.DoesNotExist:
                booking = None
                user = None
            booking_date_parse = parse(booking_date)
            booking_date_weekday = booking_date_parse.weekday()
            start_date = booking_date_parse - timedelta(days=booking_date_weekday)
            end_date = booking_date_parse + timedelta(days=(5 - booking_date_weekday))
            request_real_name = request.user.profile.real_name
            if Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청')).count() < 1000:
                Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status, booking_rn=booking_rn).save()
                return redirect(reverse('superapp:supercreate2'))
            else:
                errors.append('주 2회 예약이 넘었는지 확인하세요.')
                return render(request, 'superapp/supercreate2.html', {'errors': errors})
        return render(request, 'superapp/supercreate2.html', context)
    elif not request.user.is_superuser:
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
        errors = []
        if request.method == 'POST':
            booking_date = request.POST.get('date')
            booking_time = request.POST.get('time')
            booking_status = request.POST.get('status')
            booking_rn = request.POST.get('booking_rn')
            try:
                booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
                if booking_status == '예약요청':
                    user = booking.user
                    booking.delete()
                elif booking_status == '예약승인':
                    user = booking.user
                    recipient_id = booking.user_id
                    if user:
                        message = f"{user.profile.real_name}님, {booking_date} {booking_time}의 예약이 승인되었습니다."
                        recipient = User.objects.get(id=recipient_id)
                        sender = request.user
                        note = Note.objects.create(sender=sender, recipient=recipient, message=message)
                    booking.delete()
                elif booking_status == '예약가능':
                    booking.delete()
                    user = None
                elif booking_status == '예약불가':
                    booking.delete()
                    user = None
            except Booking.DoesNotExist:
                booking = None
                user = None
            booking_date_parse = parse(booking_date)
            booking_date_weekday = booking_date_parse.weekday()
            start_date = booking_date_parse - timedelta(days=booking_date_weekday)
            end_date = booking_date_parse + timedelta(days=(5 - booking_date_weekday))
            request_real_name = request.user.profile.real_name
            if Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청')).count() < 1000:
                Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status, booking_rn=booking_rn).save()
                return redirect(reverse('superapp:supercreate2_1'))
            else:
                errors.append('주 2회 예약이 넘었는지 확인하세요.')
                return render(request, 'superapp/supercreate2_1.html', {'errors': errors})
        return render(request, 'superapp/supercreate2_1.html', context)
    elif not request.user.is_superuser:
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
                msg_2 = f"{name}님, {date} {time}분의 예약이 승인되었습니다."
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
                msg_2 = f"{name}님, {date} {time}분의 예약이 승인되었습니다."
                aligo_sms_send(rec, msg_2)
            elif str(msg)=='cancel':
                msg_2 = f"{name}님, {date} {time}분의 예약이 취소되었습니다."
                aligo_sms_send(rec, msg_2)
        return render(request, 'superapp/supercreate4.html', context)
    elif not request.user.is_superuser:
        return redirect(reverse('articleapp:index'))


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

