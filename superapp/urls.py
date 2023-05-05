from django.urls import path

from superapp.views import superbooking, superbooking2, superbooking3, superbooking4, superbooking2_1

app_name = 'superapp'

urlpatterns = [
    path('supercreate/', superbooking, name='supercreate'),
    path('supercreate2/', superbooking2, name='supercreate2'),
    path('supercreate2_1/', superbooking2_1, name='supercreate2_1'),
    path('supercreate3/', superbooking3, name='supercreate3'),
    path('supercreate4/', superbooking4, name='supercreate4'),
]