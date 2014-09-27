from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from truco.constants import *



class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)


class RegisterForm(UserCreationForm):
# Personalizamos la clase UserCreationForm
    email = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class crear_partida_form(forms.Form):
    nombre = forms.CharField(max_length=32,required=True)
    puntos_objetivo = forms.ChoiceField(
            widget=forms.RadioSelect, choices=PUNTOS_OBJETIVO, required=True
            )
    password = forms.CharField(widget=forms.PasswordInput, required=False)

