import re
from django import forms
from django.forms import ModelForm
from profileapp.models import Profile

REAL_NAME_RE = re.compile(r'^[가-힣A-Za-z\s]{2,16}$')
BIRTH_DATE_RE = re.compile(r'^[0-9-]{6,10}$')
PHONE_NUM_RE = re.compile(r'^[0-9-\s]{7,16}$')


def _validate_real_name(value):
    cleaned = (value or '').strip()
    if not REAL_NAME_RE.fullmatch(cleaned):
        raise forms.ValidationError('성명은 2~16자의 한글 또는 영문으로 입력해 주세요.')
    return cleaned


def _validate_birth_date(value):
    cleaned = (value or '').strip()
    if not BIRTH_DATE_RE.fullmatch(cleaned):
        raise forms.ValidationError('생년월일은 숫자로 입력해 주세요. (예: 900101)')
    return cleaned


def _validate_phone_num(value):
    cleaned = (value or '').strip()
    if not PHONE_NUM_RE.fullmatch(cleaned):
        raise forms.ValidationError('전화번호는 숫자와 하이픈(-)만 입력해 주세요. (예: 010-1234-5678)')
    return cleaned


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

    def clean_real_name(self):
        return _validate_real_name(self.cleaned_data.get('real_name'))

    def clean_birth_date(self):
        return _validate_birth_date(self.cleaned_data.get('birth_date'))

    def clean_phone_num(self):
        return _validate_phone_num(self.cleaned_data.get('phone_num'))


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

    def clean_birth_date(self):
        return _validate_birth_date(self.cleaned_data.get('birth_date'))

    def clean_phone_num(self):
        return _validate_phone_num(self.cleaned_data.get('phone_num'))