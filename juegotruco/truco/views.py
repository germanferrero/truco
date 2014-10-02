from django.shortcuts import render, redirect
from django.template import RequestContext, loader, Context
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
    lobby = Lobby()
    lista_de_partidas = lobby.get_lista_partidas()
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
            lobby = Lobby()
            partida = lobby.crear_partida(request.user,
                                                form.cleaned_data['nombre'],
                                                form.cleaned_data['puntos_objetivo'],
                                                form.cleaned_data['password'])
            return redirect(reverse('truco:partida', args=(partida.id,)))
        else:
            # Si el formulario es incorrecto se muestran los errores.
            return render(request, 'truco/crear_partida.html',{'form': form})
    else:
        # SI hay un GET se muestra el formulario para crear partida.
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html', {'form': form})


@login_required(login_url='/usuarios/login')
def unirse_partida(request):
    partida = Partida.get(request.POST['partida'])
    lobby = Lobby()
    if lobby.unirse_partida(request.user,partida) == -1:
        return redirect(reverse('truco:lobby'))
    else:
        partida.actualizar_estado()
        return redirect(reverse('truco:en_espera', args=(partida.id,)))


@login_required(login_url='/usuarios/login')
def partida(request,partida_id):
    partida = Partida.get(partida_id)
    if partida:
        if partida.is_ready():
            ronda = partida.crear_ronda()
            return redirect(reverse('truco:ronda', args=(partida.id,)))
        else:
            context = {'partida' : partida,
                       'puntajes' : partida.get_puntajes(request.user),
                       'username' : request.user.username,
                       'mensaje_ganador' : partida.get_mensaje_ganador(request.user)}
            return render(request,'truco/partida.html',context)
    else:
        return redirect(reverse('truco:index'))


def en_espera(request,partida_id):
    partida = Partida.get(partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)
    if ronda and jugador == ronda.get_turno():
        return redirect(reverse('truco:ronda', args=(partida_id,)))
    else:
        context = Context({'puntajes' : partida.get_puntajes(request.user),
                           'partida' : partida,
                           'username' : request.user.username
                           })
        if ronda:
            context['ronda'] = ronda
            context['cartas_disponibles'] = jugador.get_cartas_diponibles()
            context['cartas_jugadas'] = jugador.get_cartas_jugadas()
            context['cant_cartas_adversario'] = ([i+1 for i in range(ronda.cant_cartas_adversario(jugador))])
            context['cartas_jugadas_adversario'] = ronda.cartas_jugadas_adversario(jugador)
            context['mensaje_envido'] = ronda.get_mensaje_ganador_envido(jugador)
        return render(request,'truco/en_espera.html', context)

def ronda(request,partida_id):
    partida = Partida.get(partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)
    if request.method == "POST":
        if 'opcion' in request.POST:
            opcion = int(request.POST['opcion'])
            if opcion == CANTAR_ENVIDO:
                canto = ronda.crear_canto(ENVIDO, jugador)
                return redirect(reverse('truco:en_espera', args=(partida.id,)))
            elif opcion == CANTAR_TRUCO:
                canto = ronda.crear_canto(TRUCO, jugador)
                return redirect(reverse('truco:en_espera', args=(partida.id,)))
            elif opcion == QUIERO or opcion == NO_QUIERO:
                return redirect(reverse('truco:responder_canto', args=(partida.id,opcion,)))
        elif 'carta' in request.POST:
            return redirect(reverse('truco:tirar_carta', args=(partida.id,request.POST['carta'],)))
    else:
        context = {'puntajes' : partida.get_puntajes(request.user),
                    'partida' : partida,
                    'username' : request.user.username,
                    'ronda' : ronda,
                    'cartas_disponibles' : jugador.get_cartas_diponibles(),
                    'cartas_jugadas' : jugador.get_cartas_jugadas(),
                    'cant_cartas_adversario' : [i+1 for i in range(ronda.cant_cartas_adversario(jugador))],
                    'cartas_jugadas_adversario' : ronda.cartas_jugadas_adversario(jugador),
                    'opciones' : ronda.get_opciones(),
                    'op_dict' : OPCIONES,
                    'puntajes' : partida.get_puntajes(request.user),
                    'mensaje_envido': ronda.get_mensaje_ganador_envido(jugador)
                  }
        return render(request,'truco/ronda.html', context)


def tirar_carta(request, partida_id, carta_id):
    partida = Partida.get(partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)
    ultimo_enfrentamiento = ronda.get_ultimo_enfrentamiento()
    carta = Carta.objects.get(pk=carta_id)
    if not ultimo_enfrentamiento or ultimo_enfrentamiento.get_termino():
        # Si no hay un enfrentamiento o el ultimo enfrentamiento ya esta terminado
        # Se crea un enfrentamiento nuevo
        ultimo_enfrentamiento = ronda.crear_enfrentamiento(jugador)
    ultimo_enfrentamiento.agregar_carta(Carta.objects.get(id=carta_id))
    jugador.cartas_disponibles.remove(carta)
    jugador.cartas_jugadas.add(carta)
    return redirect(reverse('truco:en_espera', args=(partida.id,)))


def responder_canto(request, partida_id, opcion):
    partida = Partida.get(partida_id)
    ronda = partida.get_ronda_actual()
    canto_actual = ronda.get_ultimo_canto()
    if int(opcion) == QUIERO:
        canto_actual.aceptar()
        if canto_actual.tipo == ENVIDO:
            canto_actual.envido.get_ganador()
            canto_actual.save()
    else:
        print "MIRA"
        canto_actual.rechazar()
        canto_actual.save()
    return redirect(reverse('truco:en_espera', args=(partida.id,)))


