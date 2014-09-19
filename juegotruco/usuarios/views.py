from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from usuarios.forms import LoginForm, RegisterForm
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required


def my_login(request):
    if request.method == 'POST':
        # Si hay un POST, se instancia un RegisterForm con los datos completados
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
        # Si los datos son invalidos mustra mensaje de error y el formulario
        else:
            return TemplateResponse(request, 'usuarios/login.html',
                    {'form':form})

        return HttpResponseRedirect(reverse('truco:lobby'))
    else:
        # Si hay un GET, se muestran los campos a completar
        form = LoginForm()
    return TemplateResponse(request, 'usuarios/login.html',
                            {'form':form})

def my_create_user(request):
    if request.method == 'POST':
        # Si hay un POST, se instancia un RegisterForm con los datos completados
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            # Se crea un nuevo usuario
            User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                )
            # Se loguea al usuario recien creado
            new_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
                )
            login(request, new_user)
        else:
            return TemplateResponse(request, 'usuarios/create_user.html',
                                    {'form':form})
        return HttpResponseRedirect(reverse('truco:lobby'))
    else:
        # Si hay un GET, se muestran los campos a completar
        form = RegisterForm()
    return TemplateResponse(request, 'usuarios/create_user.html',
                            {'form':form})

def my_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('truco:lobby'))
