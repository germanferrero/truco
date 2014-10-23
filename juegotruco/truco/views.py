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

"""
View Lobby: Se muestran las partidas donde aun hay lugar para mas jugadores.
"""
@login_required(login_url='/usuarios/login')
def lobby(request):
    lobby = Lobby()
    lista_de_partidas = lobby.get_lista_partidas()
    context = {'lista_de_partidas': lista_de_partidas,
               'username': request.user.username}
    return render(request, 'truco/lobby.html',context)

"""
View index: Es la unica view de la aplicacion truco que puede accederse sin estar
logueado, caso en el cual redirecciona al login. Si el usuario esta logueado lo
redirige al lobby.
"""
def index(request):
        # Si esta logueado entra al lobby directamente
        return redirect(reverse('truco:lobby'))

"""
View crear una partida: muestra el formulario para crear una nueva partida.
Los campos nombre y puntos objetivo son obligatorios. El campo password es opcional.
"""
@login_required(login_url='/usuarios/login')
def crear_partida(request):
    if request.method == "POST":
        form = crear_partida_form(data=request.POST)
        if form.is_valid():
            # Si se llenaron los campos obligatorios
            lobby = Lobby()
            partida = lobby.crear_partida(request.user,
                                                form.cleaned_data['nombre'],
                                                form.cleaned_data['puntos_objetivo'],
                                                form.cleaned_data['password'])
            return redirect(reverse('truco:partida', args=(partida.id,)))
        else:
            # Si el formulario es incorrecto se muestran los errores
            return render(request, 'truco/crear_partida.html',{'form': form})
    else:
        # SI hay un GET se muestra el formulario para crear partida
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html', {'form': form})

"""
View unirse a una partida: Si se selecciona una partida a la que se puede ingresar,
se redirige al usuario a la partida en la vista "en espera". Si no, si lo vuelve al lobby.
El usuario no puede ingresar a una partida si no selecciono una partida de la lista
que se muestra en el lobby o si ya tiene un jugador en la partida que eligio.
"""
@login_required(login_url='/usuarios/login')
def unirse_partida(request):
    partida = request.POST.get('partida', False)
    if partida:
        lobby = Lobby()
        partida = Partida.objects.get(pk=request.POST['partida'])
        if lobby.unirse_partida(request.user,partida) == -1:
            # Si no puedo unirme a la partida
            return redirect(reverse('truco:lobby'))
        else:
            # Si selecciona una partida a la que puede ingresar
            partida.actualizar_estado()
            return redirect(reverse('truco:en_espera', args=(partida.id,)))
    else:
        # No se selecciono una partida
        return redirect(reverse('truco:lobby'))

"""
View partida: Se encarga de definir cuando la partida debe continuar o terminar.
Si se termina se redirige a la view index, si no, crea una nueva ronda.
"""
@login_required(login_url='/usuarios/login')
def partida(request,partida_id):
    partida = Partida.objects.get(pk=partida_id)
    if partida:
        # La partida existe
        if partida.get_ganador() < 0:
            # No hay un ganador de la partida
            partida.actualizar_puntajes()
        if partida.is_ready():
            # Si no hay un ganador y no hay una ronda en curso y los jugadores estan listos
            ronda = partida.crear_ronda()
            partida.actualizar_mano()  # Se le da la mano al jugador de la derecha
            return redirect(reverse('truco:en_espera', args=(partida.id,)))
        else:
            context = {'partida' : partida,
                       'puntajes' : partida.get_puntajes(request.user),
                       'username' : request.user.username,
                       'mensaje_ganador' : partida.get_mensaje_ganador(request.user)}
            return render(request,'truco/partida.html',context)
    else:
        return redirect(reverse('truco:index'))

"""
View en espera: Se redirigen los jugadores a esta vista cuando no es su turno.
Aqui solo se puede ver las cartas propias, las ya jugadas en la mesa y el mensaje
del resultado del envido.
"""
@login_required(login_url='/usuarios/login')
def en_espera(request,partida_id):
    partida = Partida.objects.get(pk=partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)  # jugador del usuario
    if partida.get_ganador() >= 0:
        return redirect(reverse('truco:partida', args=(partida_id,)))
    elif ronda and jugador == ronda.get_turno():
        # Si hay una ronda en curso y es el turno del jugador
        return redirect(reverse('truco:ronda', args=(partida_id,)))
    else:
        context = Context({'puntajes' : partida.get_puntajes(request.user),
                           'partida' : partida,
                           'username' : request.user.username
                           })
        if ronda:
            context['ronda'] = ronda
            context['cartas_disponibles'] = jugador.get_cartas_diponibles()
            context['cartas_jugadas'] = ronda.get_cartas_jugadas(jugador)
            context['cant_cartas_adversario'] = ([i+1 for i in range(ronda.cant_cartas_adversario(jugador))])
            context['mensaje_envido'] = ronda.get_mensaje_ganador_envido(jugador)
            context['mensaje_canto'] = ronda.get_mensaje_canto()
        return render(request,'truco/en_espera.html', context)

"""
View ronda: Se muestran las opciones de juego que tiene un jugador en turno.
Se evalua la opcion elegida y se redirige al jugador a la view "en espera"
si canta, a la view responder canto si hay un canto no respondido y a la view tirar
carta si eligio tirar una carta. Si hay un ganador, se lo redirige a la partida.
"""
@login_required(login_url='/usuarios/login')
def ronda(request,partida_id):
    partida = Partida.objects.get(pk=partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)
    if request.method == "POST":
        # El jugador eligio una opcion
        if 'opcion' in request.POST:
            opcion = int(request.POST['opcion'])
            if opcion == QUIERO or opcion == NO_QUIERO:
                return redirect(reverse('truco:responder_canto', args=(partida.id,opcion,)))
            else:
                ronda.crear_canto(opcion,jugador)
                return redirect(reverse('truco:en_espera', args=(partida.id,)))
        elif 'carta' in request.POST:
            return redirect(reverse('truco:tirar_carta', args=(partida.id,request.POST['carta'],)))
    else:
        if not ronda.hay_ganador():
            # Si no se termino la ronda muestra las opciones
            context = {'puntajes' : partida.get_puntajes(request.user),
                        'partida' : partida,
                        'username' : request.user.username,
                        'ronda' : ronda,
                        'cartas_disponibles' : jugador.get_cartas_diponibles(),
                        'cartas_jugadas' : ronda.get_cartas_jugadas(jugador),
                        'cant_cartas_adversario' : [i+1 for i in range(ronda.cant_cartas_adversario(jugador))],
                        'opciones' : ronda.get_opciones(),
                        'op_dict' : OPCIONES,
                        'puntajes' : partida.get_puntajes(request.user),
                        'mensaje_envido': ronda.get_mensaje_ganador_envido(jugador),
                        'mensaje_canto' : ronda.get_mensaje_canto(),
                        'puede_tirar_carta' : ronda.se_puede_tirar()
                      }
            return render(request,'truco/ronda.html', context)
        else:  # Se termino la ronda
            return redirect(reverse('truco:partida', args=(partida.id,)))

"""
View tirar carta: Maneja el caso donde la opcion elegida por el jugador en turno
(view ronda) elige tirar una carta. Si no se termino la ronda, se crea un nuevo
enfrentamiento. Si no se termino el enfrentamiento, agrega una carta y lo da por terminado.
"""
@login_required(login_url='/usuarios/login')
def tirar_carta(request, partida_id, carta_id):
    partida = Partida.objects.get(pk=partida_id)
    ronda = partida.get_ronda_actual()
    jugador = partida.find_jugador(request.user)
    ultimo_enfrentamiento = ronda.get_ultimo_enfrentamiento()
    carta = Carta.objects.get(pk=carta_id)
    if not ultimo_enfrentamiento or ultimo_enfrentamiento.get_termino():
        # Si no hay un enfrentamiento o el ultimo enfrentamiento ya esta terminado
        ultimo_enfrentamiento = ronda.crear_enfrentamiento(jugador)
        # Se crea un enfrentamiento nuevo
    ultimo_enfrentamiento.agregar_carta(Carta.objects.get(id=carta_id))
    jugador.cartas_disponibles.remove(carta)
    return redirect(reverse('truco:en_espera', args=(partida.id,)))

"""
View responder canto: Si hay un canto activo se redirige al jugador en turno a esta
view. Se le muestran las opciones disponibles y se redirecciona a "en espera" luego
de que elija la opcion.
"""
@login_required(login_url='/usuarios/login')
def responder_canto(request, partida_id, opcion):
    partida = Partida.objects.get(pk=partida_id)
    ronda = partida.get_ronda_actual()
    canto_actual = ronda.get_ultimo_canto()
    if int(opcion) == QUIERO:
        canto_actual.aceptar()
    else:
        canto_actual.rechazar()
    return redirect(reverse('truco:en_espera', args=(partida.id,)))
