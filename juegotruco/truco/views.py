from django.shortcuts import render, redirect
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from truco.models import Lobby, Partida, Jugador, Carta, Ronda
from truco.constants import *
from truco.forms import crear_partida_form
from django.dispatch import receiver

@login_required(login_url='/usuarios/login')
def lobby(request):
    my_lobby = Lobby()
    lista_de_partidas = my_lobby.get_lista_partidas()
    context = {'lista_de_partidas': lista_de_partidas,
               'username': request.user.username}
    return render(request, 'truco/lobby.html',context)


def index(request):
    if request.method == 'POST':
        # Si hay un POST, se redirecciona a login o create_user
        url = data=request.POST
        return redirect(request, url)  #'truco/index.html')
    else:
        # Si esta logueado entra al lobby directamente
        return redirect(reverse('truco:lobby'))


@login_required(login_url='/usuarios/login')
def crear_partida(request):
    if request.method == "POST":
        form = crear_partida_form(data=request.POST)
        if form.is_valid():
            my_lobby = Lobby()
            my_partida = my_lobby.crear_partida(request.user,
                                                form.cleaned_data['nombre'],
                                                form.cleaned_data['puntos_objetivo'],
                                                form.cleaned_data['password'])
            return redirect('partida/%d' % int(my_partida.id))
        else:
            # Si el formulario es incorrecto se muestran los errores.
            return render(request, 'truco/crear_partida.html',{'form': form})
    else:
        # SI hay un GET se muestra el formulario para crear partida.
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html', {'form': form})


@login_required(login_url='/usuarios/login')
def unirse_partida(request):
    my_partida = Partida.get(request.POST['partida'])
    my_lobby = Lobby()
    if my_lobby.unirse_partida(request.user,my_partida) == -1:
        return redirect(reverse('truco:lobby'))
    else:
        return redirect('en_espera/%d' % int(my_partida.id))


@login_required(login_url='/usuarios/login')
def partida(request,partida_id):
    partida = Partida.get(partida_id)
    if partida:
        if partida.is_ready():
            ronda = partida.crear_ronda()
            return redirect(ronda)
        else:
            context = {'puntajes' : partida.get_puntajes(request.user),
                        'username' : request.user.username,
                        'partida' : partida}
            return render(request,'truco/partida.html',context)
    else:
        return redirect(reverse('index'))


def en_espera(request,partida_id):
    partida = Partida.get(partida_id)
    ronda = partida.get_ronda_actual()
    jugador = ronda.find_jugador(request.user)
    if ronda and jugador == ronda.get_turno():
        return redirect(ronda.get_instancia())
    else:
        context = {'ronda' : ronda,
                    'cartas_disponibles' : jugador.get_cartas_diponibles(),
                    'cartas_jugadas' : jugador.get_cartas_jugadas(),
                    'cant_cartas_adversario' : ronda.cant_cartas_adversario(jugador),
                    'cartas_jugadas_adversario' : ronda.cartas_jugadas_adversario(jugador),
                  }
        return render(request,'truco/en_espera.html',{})

def ronda(request,ronda_id):
    ronda = Ronda.get(ronda_id)
    jugador = ronda.find_jugador(request.user)
    if request.method == POST:
        if 'opcion' in request.POST:
            opcion = request.POST['opcion']
            if opcion == "CANTAR ENVIDO":
                canto = ronda.crear_canto(ENVIDO, my_jugador)
                return redirect(canto)
            elif opcion == "CANTAR TRUCO":
                canto = my_ronda.crear_canto(TRUCO, my_jugador)
                return redirect(canto)
        elif 'carta' in request.POST:
            ultimo_enfrentamiento = ronda.get_ultimo_enfrentamiento()
            if ultimo_enfrentamiento and not ultimo_enfrentamiento.termino:
                return redirect(ultimo_enfrentamiento)
            else:
                enfrentamiento = ronda.crear_enfrentamiento(jugador,
                                                            request.POST['carta'])
                return redirect(enfrentamiento)
    else:
        context = {'ronda' : ronda,
                    'cartas_disponibles' : jugador.get_cartas_diponibles(),
                    'cartas_jugadas' : jugador.get_cartas_jugadas(),
                    'cant_cartas_adversario' : ronda.cant_cartas_adversario(jugador),
                    'cartas_jugadas_adversario' : ronda.cartas_jugadas_adversario(jugador),
                    'opciones' : ronda.get_opciones()
                  }
        return render(request,'truco/ronda.html',context)
