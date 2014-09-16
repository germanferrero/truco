from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from truco.forms import LoginForm, UserCreationForm
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


def my_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
        return HttpResponseRedirect('/truco/index')
    else:
        form = LoginForm()
    return TemplateResponse(request, 'truco/login.html',
                            {'form':form})

@login_required(login_url='/truco/login')
def index(request):
    return HttpResponse("LOGUEADO!!")

def my_create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(request.POST['username'],
                                            request.POST['password1'],
                                            request.POST['password2'],
                                            )
        return HttpResponseRedirect('/truco/index')
    else:
        form = UserCreationForm()
    return TemplateResponse(request, 'truco/create_user.html',
                            {'form':form})

def my_logout(request):
    logout(request)
    return HttpResponse("DESLOGUEADO!")
