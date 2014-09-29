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
        return HttpResponseRedirect(request, url)  #'truco/index.html')
    else:
        # Si esta logueado entra al lobby directamente
        return HttpResponseRedirect(reverse('truco:lobby'))


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
            return HttpResponseRedirect('partida/%d' % int(my_partida.id))
        else:
            # Si el formulario es incorrecto se muestran los errores.
            return TemplateResponse(request, 'truco/crear_partida.html',
                                    {'form': form})
    else:
        # SI hay un GET se muestra el formulario para crear partida.
        form = crear_partida_form()
        return render(request, 'truco/crear_partida.html', {'form': form})


@login_required(login_url='/usuarios/login')
def unirse_partida(request):
    my_partida = Partida.objects.get(pk=request.POST['partida'])
    my_lobby = Lobby()
    if my_lobby.unirse_partida(request.user,my_partida) == -1:
        return HttpResponseRedirect(reverse('truco:lobby'))
    else:
        return HttpResponseRedirect('partida/%d' % int(my_partida.id))


@login_required(login_url='/usuarios/login')
def partida(request,partida_id):
    my_partida = Partida.objects.get(id=partida_id)
    my_jugador = my_partida.jugadores.get(user=request.user)
    my_ronda = list(my_partida.ronda_set.all())
    my_opciones = []
    mensaje = ""
    if my_ronda:
        my_ronda = my_ronda[-1]
        ###################################################
        # Lo que esta entre estos simbolos sirve para mostrar el mensaje del ganador del envido.
        ultimo_canto = list(my_ronda.canto_set.all())[-1:]
        if ultimo_canto and ultimo_canto[0].tipo == str(ENVIDO) and ultimo_canto[0].pts_en_juego > 1:
        # En caso de que se haya aceptado el envido
            ultimo_canto = ultimo_canto[0]
            mensaje = "El equipo ganador es "+str(my_partida.jugadores.get(equipo=ultimo_canto.equipo_ganador))+" con "+str(ultimo_canto.puntos_ganador)+"puntos"
        ##################################################
        if my_ronda.turno == list(my_partida.jugadores.all()).index(my_jugador): # CAMBIAR! EN ESTE MOMENTO, LAS CARTAS SON BOTONES ACTIVOS! ENTONCES PODES PULSARLAS CUANDO ES EL TURNO DEL OTRO! SI SE VUELVEN INACTIVOS, HAY QUE SACAR ESTA LINEA
        # Es mi turno
            if request.method == 'POST':
                if 'opcion' in request.POST:
                # Si el jugador elige una opcion del costado
                    opcion = request.POST['opcion']
                    if opcion == "CANTAR ENVIDO":
                        my_ronda.crear_canto(PTS_CANTO[ENVIDO], my_jugador)
                    elif opcion == "CANTAR TRUCO":
                        my_ronda.crear_canto(PTS_CANTO[TRUCO], my_jugador)
                    else:
                        my_ronda.responder_canto(opcion)
                elif 'carta' in request.POST:
                # Si el jugador elige una carta para tirar
                    my_partida.tirar(my_jugador, Carta.objects.get(id=request.POST['carta']))
            # Se establecen las opciones para mostrarle al jugador
            if my_ronda.turno == list(my_partida.jugadores.all()).index(my_jugador):
                my_opciones = my_ronda.opciones
                my_opciones = map(lambda x: OPCIONES[int(x)], my_opciones)
    # Muestra las cartas del adversario
    adversario = [i for i in my_partida.jugadores.all() if i != my_jugador]
    adv_cartas_disponibles = []
    if adversario:
        adv_cartas_disponibles = list(adversario[0].cartas.all())
    my_cartas_disponibles = my_jugador.cartas_disponibles.all()
    context = {'partida': my_partida,
                'my_cartas_disponibles': my_cartas_disponibles,
                'adv_cartas_disponibles': [i+1 for i in range(len(adv_cartas_disponibles))],
                'username': request.user.username,
                'opciones': my_opciones,
                'mensaje': mensaje,}
    return TemplateResponse(request, 'truco/partida.html',context)
