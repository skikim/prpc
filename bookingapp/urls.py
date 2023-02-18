from django.urls import path

from bookingapp.views import booking, BookingDetailView, booking_delete, booking_2

app_name = 'bookingapp'

urlpatterns = [
    path('create/', booking, name='create'),
    path('create2/', booking_2, name='create2'),
    path('detail<int:pk>/', BookingDetailView.as_view(), name='detail'),
    path('delete<int:pk>/', booking_delete, name='delete'),
]