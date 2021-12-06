import re

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.core.exceptions import ValidationError

from main.models import User, Order


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class OrderForm(forms.ModelForm):
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise ValidationError("Введите Ваше имя")

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError("Введите Ваш телефон")
        if not bool(re.match(r"^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$", phone)):
            raise ValidationError("Введите Ваш номер корректно")

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise ValidationError("Введите Ваш адрес")

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'address', "buying_type", "comment"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={'cols': 60, 'rows': 10}),
        }
