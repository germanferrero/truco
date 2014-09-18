from django.shortcuts import render
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

@login_required(login_url='/usuarios/login')
def lobby(request):
    return TemplateResponse(request, 'truco/lobby.html')

