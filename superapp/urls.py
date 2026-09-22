from django.urls import path

from superapp.views import superbooking, superbooking2, superbooking3, superbooking4, superbooking2_1, superbooking2_2, block_online_bookings, unblock_online_bookings, tablet_booking, tablet_booking2, tablet_booking3, tablet_status, tablet_pending, tablet_slots, waiting_pt, waiting_pt_status, waiting_list, waiting_list_status

app_name = 'superapp'

urlpatterns = [
    path('pending-selections/', tablet_pending, name='tablet_pending'),
    path('tablet/status/', tablet_status, name='tablet_status'),
    path('tablet/slots/', tablet_slots, name='tablet_slots'),
    path('tablet/', tablet_booking, name='tablet'),
    path('tablet2/', tablet_booking2, name='tablet2'),
    path('tablet3/', tablet_booking3, name='tablet3'),
    path('waiting_pt/status/', waiting_pt_status, name='waiting_pt_status'),
    path('waiting_pt/', waiting_pt, name='waiting_pt'),
    path('waiting_list/status/', waiting_list_status, name='waiting_list_status'),
    path('waiting_list/', waiting_list, name='waiting_list'),
    path('supercreate/', superbooking, name='supercreate'),
    path('supercreate2/', superbooking2, name='supercreate2'),
    path('supercreate2_1/', superbooking2_1, name='supercreate2_1'),
    path('supercreate2_2/', superbooking2_2, name='supercreate2_2'),
    path('supercreate3/', superbooking3, name='supercreate3'),
    path('supercreate4/', superbooking4, name='supercreate4'),
    path('block-bookings/', block_online_bookings, name='block_bookings'),
    path('unblock-bookings/', unblock_online_bookings, name='unblock_bookings'),
]