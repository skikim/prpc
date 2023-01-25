from django.forms import ModelForm
from profileapp.models import Profile


class ProfileCreationForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['birth_date', 'phone_num']
        labels = {
            'birth_date': ('주민번호 앞6자리'),
            'phone_num': ('폰번호')
        }
        help_texts = {
            # 'birth_date': ('주민번호 앞6자리'),
            'phone_num': ('예) 010-1234-5678')
        }