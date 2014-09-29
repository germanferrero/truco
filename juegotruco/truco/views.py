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
    if request.method == 'POST':
        print 'POST'
    if my_ronda:
        my_ronda = my_ronda[-1]
        if my_ronda.turno == list(my_partida.jugadores.all()).index(my_jugador):
            if request.method == 'POST':
                print "POST en mi turno"
                # Parseo de request.POST para ver opciones elegidas
                temp_list = []
                for key, value in request.POST.iteritems():
                    temp = [key,value]
                    temp_list.append(temp)
                [item for post_list in temp_list for item in post_list]
                print post_list
                # Si el jugador elige una opcion del costado:
                if any(u'opcion' in s for s in post_list):
                    opcion = request.POST['option']
                    #print request.POST['opcion']
                    if opcion == "CANTAR ENVIDO":
                        my_ronda.crear_canto(PTS_CANTO[1], my_jugador)
                    elif opcion == "CANTAR TRUCO":
                        my_ronda.crear_canto(PTS_CANTO[0], my_jugador)
                    else:
                        my_ronda.responder_canto(opcion)
                # Si el jugador elige una carta para tirar
                elif any(u'carta' in s for s in post_list):
                    print "post_list", post_list[0][5:]
                    my_partida.tirar(my_jugador, Carta.objects.get(id=post_list[0][5:]))
            # Se establecen las opciones para mostrarle al jugador
            print "my_opcion", my_opciones
            my_opciones = my_ronda.opciones
            my_opciones = map(lambda x: OPCIONES[int(x)], my_opciones)
    adversario = [i for i in my_partida.jugadores.all() if i != my_jugador]
    adv_cartas_disponibles = []
    if adversario:
        adv_cartas_disponibles = list(adversario[0].cartas.all())
    my_cartas_disponibles = my_jugador.cartas_disponibles.all()
    context = {'partida': my_partida,
                'my_cartas_disponibles': my_cartas_disponibles,
                'adv_cartas_disponibles': [i+1 for i in range(len(adv_cartas_disponibles))],
                'username': request.user.username,
                'opciones': my_opciones,}
    return TemplateResponse(request, 'truco/partida.html',context)
