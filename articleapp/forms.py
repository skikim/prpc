from django.forms import ModelForm

from articleapp.models import Waiting


class WaitingCreationForm(ModelForm):
    class Meta:
        model = Waiting
        fields = ['waiting_num',]
        labels = {
            'waiting_num': '대기자 수',
        }


# class HolidayCreateForm(ModelForm):
#     class Meta:
#         model = Holiday
#         fields = ['holiday_message']