from django.shortcuts import render
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from truco.models import Lobby, Partida, Jugador
from truco.forms import crear_partida_form

@login_required(login_url='/usuarios/login')
def lobby(request):
    my_lobby = Lobby()
    lista_de_partidas = my_lobby.get_lista_partidas()
    context = {'lista_de_partidas': lista_de_partidas}
    return render(request, 'truco/lobby.html',context)


def index(request):
    if request.method == 'POST':
        # Si hay un POST, se redirecciona a login o create_user
        url = data=request.POST
        return HttpResponseRedirect(request, url)  #'truco/index.html')
    else:
        # Si hay un GET, se muestran la pagina
        return TemplateResponse(request, 'truco/index.html', {})

def crear_partida(request):
    if request.method == "POST":
        pass
    else:
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html',
                                {'form': form})

def unirse_partida(request):
    return HttpResponse("Unirse Partida")
