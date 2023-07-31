import datetime
from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView

from articleapp.models import Holiday
from bookingapp.decorators import booking_ownership_required
from bookingapp.models import Booking
import requests

from noteapp.models import Note
from django.contrib.auth.models import User


# Create your views here.

has_ownership = [
    login_required, booking_ownership_required
]


def send_message(msg):
    TARGET_URL = 'https://notify-api.line.me/api/notify'
    TOKEN = 'xngZHmAg4YXdRgIqMb0Rq9d7jERLOwGe1Es6jd76cJo'		# 내가 발급받은 토큰
    headers={'Authorization': 'Bearer ' + TOKEN}
    now = datetime.datetime.now()
    data={'message': f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    response = requests.post(TARGET_URL, headers=headers, data=data)


def send_message_2(msg):
    TARGET_URL = 'https://notify-api.line.me/api/notify'
    TOKEN = 'QGfhpZOSYthQBxVhEB5UP7lC75XyWCEtMg8VsTwqrqY'  # 장은미씨 발급받은 토큰
    headers = {'Authorization': 'Bearer ' + TOKEN}
    now = datetime.datetime.now()
    data = {'message': f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    response = requests.post(TARGET_URL, headers=headers, data=data)


    # """디스코드 메세지 전송"""
    # DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1071627279836397578/7yNetkPT0o1gX8TTMuJHXce6CjbovaY7RyOqwEoEOJtMYS72Kx6A7GKFH2n1jl4_phws"
    # dt_now = datetime.datetime.now()
    # message = {"content": f"[{dt_now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    # requests.post(DISCORD_WEBHOOK_URL, data=message)
    # print(message)


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
        booking_date_parse = parse(booking_date)
        booking_date_weekday = booking_date_parse.weekday()
        start_date = booking_date_parse - timedelta(days=booking_date_weekday)
        end_date = booking_date_parse + timedelta(days=(5 - booking_date_weekday))
        try:
            request_real_name = request.user.profile.real_name
        except:
            return redirect(reverse('profileapp:create'))
            # return redirect(reverse('accountapp:detail', kwargs={'pk': request.user.pk}))

        if Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청')).count() < 1:
            Booking.objects.get(booking_date=booking_date, booking_time=booking_time).delete()
            Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status).save()
            send_message(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
            send_message_2(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
            return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
        else:
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
        booking_date_parse = parse(booking_date)
        booking_date_weekday = booking_date_parse.weekday()
        start_date = booking_date_parse - timedelta(days=booking_date_weekday)
        end_date = booking_date_parse + timedelta(days=(5 - booking_date_weekday))
        try:
            request_real_name = request.user.profile.real_name
        except:
            return redirect(reverse('profileapp:create'))
            # return redirect(reverse('accountapp:detail', kwargs={'pk': request.user.pk}))

        if Booking.objects.filter(Q(user=user), Q(booking_date__range=(start_date, end_date)), Q(booking_status='예약승인') | Q(booking_status='예약요청')).count() < 1:
            Booking.objects.get(booking_date=booking_date, booking_time=booking_time).delete()
            Booking(booking_date=booking_date, booking_time=booking_time, user=user, booking_status=booking_status).save()
            send_message(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
            send_message_2(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 요청하셨습니다.")
            return redirect(reverse('bookingapp:detail', kwargs={'pk': user.pk}))
        else:
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
    old_booking = Booking.objects.get(booking_date=booking_date, booking_time=booking_time)
    if request.method == 'POST':
        booking.delete()
        old_booking.delete()
        send_message(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 취소하셨습니다.")
        send_message_2(f"{request_real_name}님이 {booking_date} {booking_time}의 예약을 취소하셨습니다.")

        time_format = "%H:%M"
        booking_time_datetime = datetime.datetime.strptime(booking_time, time_format)
        current_time_datetime = datetime.datetime.strptime(current_time, time_format)
        time_diff = booking_time_datetime - current_time_datetime
        # time_diff = current_time_datetime - booking_time_datetime
        print(booking_time_datetime, current_time_datetime, time_diff)
        if current_date == booking_date and time_diff < timedelta(hours=2):
            recipient_id = request_user_id
            message = f"{booking_date} {booking_time}의 예약을 예약 시간에 임박한 {current_time}에 취소하셨군요. 가능하면 하루 전에, 늦어도 2시간 전에는 꼭 취소해 주시길 당부드립니다."
            recipient = User.objects.get(id=recipient_id)
            # recipient = User.objects.get(id=28)
            sender = User.objects.get(id=1)
            note = Note.objects.create(sender=sender, recipient=recipient, message=message)

        Booking(booking_date=booking_date, booking_time=booking_time, booking_status=booking_status).save()
        return redirect(reverse('bookingapp:detail', kwargs={'pk': booking.user.pk}))
    return render(request, 'bookingapp/delete.html', {'booking' : booking})
