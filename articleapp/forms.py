from django.forms import ModelForm

from articleapp.models import Waiting


class WaitingCreationForm(ModelForm):
    class Meta:
        model = Waiting
        fields = ['waiting_num',]
        labels = {
            'waiting_num': 'λκΈ°μ μ',
        }