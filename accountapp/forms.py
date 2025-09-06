from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms


class CreateUserForm(UserCreationForm):
    terms_agreement = forms.BooleanField(
        label='이용약관과 개인정보 수집에 동의합니다.',
        required=True,
        error_messages={'required': '이용약관과 개인정보 수집에 동의해야 회원가입이 가능합니다.'}
    )
    
    class Meta:
        model = User
        fields = ['username',  'email', 'password1', 'password2']
        labels = {'username': ('아이디')}


class AccountUpdateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {'username': ('아이디')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = True


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='아이디')
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)