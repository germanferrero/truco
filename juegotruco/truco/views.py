from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from truco.forms import LoginForm
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

#template_name = 'truco/index.html'

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
    return HttpResponse("hola")

#def logout_view(request):
    #logout(request)
    ## Redirect to a success page.

