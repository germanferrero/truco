from django.shortcuts import render, redirect
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from truco.models import Lobby, Partida, Jugador
from truco.forms import crear_partida_form
from django.dispatch import receiver

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
        # Si esta logueado entra al lobby directamente
        return HttpResponseRedirect(reverse('truco:lobby'))

def crear_partida(request):
    if request.method == "POST":
        form = crear_partida_form(data=request.POST)
        if form.is_valid():
            my_lobby = Lobby()
            my_partida = my_lobby.crear_partida(request.user,
                                                form.cleaned_data['nombre'],
                                                form.cleaned_data['puntos_objetivo'],
                                                form.cleaned_data['password'])
            return HttpResponseRedirect('partida/%d' % int(my_partida.id))
        else:
            # Si el formulario es incorrecto se muestran los errores.
            return TemplateResponse(request, 'truco/crear_partida.html',
                                    {'form': form})
    else:
        # SI hay un GET se muestra el formulario para crear partida.
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html', {'form': form})

def unirse_partida(request):
    my_partida = Partida.objects.get(pk=request.POST['partida'])
    my_lobby = Lobby()
    if my_lobby.unirse_partida(request.user,my_partida) == -1:
        return HttpResponseRedirect(reverse('truco:lobby'))
    else:
        return HttpResponseRedirect('partida/%d' % int(my_partida.id))

def partida(request,partida_id):
    my_partida = Partida.objects.get(id=partida_id)
    context = {'partida': my_partida}
    return render(request, 'truco/partida.html',context)
