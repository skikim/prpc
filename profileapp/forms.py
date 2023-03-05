from django.forms import ModelForm
from profileapp.models import Profile


class ProfileCreationForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['real_name', 'birth_date', 'phone_num']
        labels = {
            'real_name': ('성명'),
            'birth_date': ('주민번호 앞6자리 (생년월일)'),
            'phone_num': ('폰번호')
        }
        help_texts = {
            # 'birth_date': ('주민번호 앞6자리'),
            'phone_num': ('예) 010-1234-5678')
        }


class ProfileUpdateForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['real_name', 'birth_date', 'phone_num']
        labels = {
            'real_name': ('성명'),
            'birth_date': ('주민번호 앞6자리 (생년월일)'),
            'phone_num': ('폰번호')
        }
        help_texts = {
            # 'birth_date': ('주민번호 앞6자리'),
            'phone_num': ('예) 010-1234-5678')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['real_name'].disabled = True