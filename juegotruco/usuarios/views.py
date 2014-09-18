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
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
            else:
                return TemplateResponse(request, 'usuarios/login.html',
                            {'form':form})

        return HttpResponseRedirect(reverse('truco:lobby'))
    else:
        form = LoginForm()
    return TemplateResponse(request, 'usuarios/login.html',
                            {'form':form})

def my_create_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(request.POST['username'],
                                            request.POST['email'],
                                            request.POST['password1'],
                                            )
        else:
            return TemplateResponse(request, 'usuarios/create_user.html',
                                    {'form':form})
        return HttpResponseRedirect('truco/lobby')
    else:
        form = RegisterForm()
    return TemplateResponse(request, 'usuarios/create_user.html',
                            {'form':form})

def my_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('truco:lobby'))
