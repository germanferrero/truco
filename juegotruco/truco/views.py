from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from truco.forms import LoginForm
from django.contrib.auth.forms import UserCreationForm
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
                return TemplateResponse(request, 'truco/login.html',
                            {'form':form})

        return HttpResponseRedirect('lobby')
    else:
        form = LoginForm()
    return TemplateResponse(request, 'truco/login.html',
                            {'form':form})

@login_required(login_url='/truco/login')
def lobby(request):
    return TemplateResponse(request, 'truco/lobby.html')

def my_create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(request.POST['username'],
                                            request.POST['password1'],
                                            request.POST['password2'],
                                            )
        else:
            return TemplateResponse(request, 'truco/create_user.html',
                                    {'form':form})
        return HttpResponseRedirect('lobby')
    else:
        form = UserCreationForm()
    return TemplateResponse(request, 'truco/create_user.html',
                            {'form':form})

def my_logout(request):
    logout(request)
    return HttpResponseRedirect('lobby')
