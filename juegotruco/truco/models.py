import random
from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from itertools import combinations
from operator import itemgetter, add


class Carta(models.Model):
    nombre = models.CharField(max_length=32)
    valor_jerarquico = models.IntegerField(max_length=2)
    valor_envido = models.IntegerField(max_length=1)
    palo = models.IntegerField(max_length=1)
    imagen = models.ImageField(upload_to='cartas', height_field=None, width_field=None)

    def __unicode__(self):
        return str(self.imagen)



class Mazo():

    def get_n_cartas(self, cant_cartas):
            return list(Carta.objects.order_by('?')[:6])



class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)
    cartas = models.ManyToManyField(Carta, related_name='cartas')
    cartas_disponibles = models.ManyToManyField(Carta, related_name='cartas_disponibles')
    cartas_jugadas = models.ManyToManyField(Carta, related_name='cartas_jugadas')

    def asignar_cartas(self, cartas):
        self.cartas_jugadas = []
        self.cartas_disponibles = cartas
        self.cartas = cartas
        self.save()

    def __str__(self):
        return self.nombre



class Lobby:

    def get_lista_partidas(self):
        lista_partidas = Partida.objects.filter(estado=EN_ESPERA)
        return (lista_partidas)

    def crear_partida(self, user, nombre, puntos_objetivo, password):
        partida = Partida(nombre=nombre, puntos_objetivo=puntos_objetivo, password=password)
        partida.save()
        jugador = partida.agregar_jugador(user)
        return partida

    def unirse_partida(self, user, partida): 
        result=0
        for j in partida.jugadores.all():
            #Verifica que el usuario no este ya en la partida
            if j.user.id == user.id:
                result=-1
        if partida.estado == EN_ESPERA and result==0:
            partida.agregar_jugador(user)
        return result



class Partida(models.Model):
    nombre = models.CharField(max_length=32)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntos_e1 = models.IntegerField(max_length=2,default=0)
    puntos_e2 = models.IntegerField(max_length=2,default=0)
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano_pos = models.IntegerField(max_length=1,default=0)
    cantidad_jugadores = models.IntegerField(default=2)

    def agregar_jugador(self,user):
            jugador = Jugador(nombre=user.username,equipo=len(self.jugadores.all())%2)
            jugador.user = user
            jugador.save()
            self.jugadores.add(jugador)
            self.save()
            if len(self.jugadores.all()) == self.cantidad_jugadores:
                self.estado = EN_CURSO
                self.crear_ronda()
                self.save()
            return jugador


    def get_absolute_url(self):
        return HttpResponseRedirect(reverse('partida'))

    def __unicode__(self):
        return self.nombre

    def crear_ronda(self):
        ronda = Ronda(partida=self)
        ronda.mano_pos = self.mano_pos
        ronda.turno = self.mano_pos
        ronda.save()
        ronda.jugadores = self.jugadores.all()
        ronda.repartir()
        ronda.save()
        self.mano_pos = (self.mano_pos +1)%self.cantidad_jugadores
        self.save()
        return ronda

    def actualizar_puntajes(self):
        ultima_ronda = list(self.ronda_set.all())[-1]
        puntos = ultima_ronda.calcular_puntos()
        self.puntos_e1 += puntos[0]
        self.puntos_e2 += puntos[1]
        if self.puntos_e1 >= self.puntos_objetivo or self.puntos_e2 >= self.puntos_objetivo:
            self.estado = FINALIZADA
        else:
            self.crear_ronda()
        self.save()

    def tirar(self,jugador,carta):
        ronda_actual = list(self.ronda_set.all())[-1]
        ronda_actual.tirar(jugador, carta)
        jugador.cartas_disponibles.remove(carta)
        jugador.cartas_jugadas.add(carta) ## COMO HACER QUE SE AGREGUEN EN ORDEN! ____
        if ronda_actual.termino:
            self.actualizar_puntajes()
        return self.estado



class Ronda(models.Model):
    # Estado inical de una ronda
    partida = models.ForeignKey(Partida, verbose_name= "partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo()
    mano_pos = models.IntegerField(max_length=1)
    turno = models.IntegerField(max_length=1, default=0)
    termino = models.BooleanField(default=False)
    id_enfrentamiento_actual = models.IntegerField(default=0)
    id_canto_actual = models.IntegerField(default=0)
    opciones = models.CharField(max_length=10, default= str(CANTAR_ENVIDO)) ## TENDRIA QUE TENER LAS OPCIONES DE ENVIDO Y TRUCO COMO DEFAULT!

    def repartir(self):
        cartas_a_repartir = self.mazo.get_n_cartas(len(self.jugadores.all())*CARTAS_JUGADOR)
        desde = 0
        for jugador in self.jugadores.all():
            hasta = desde + 3
            jugador.asignar_cartas(cartas_a_repartir[desde:hasta])
            desde = desde + 3

    def crear_enfrentamiento(self, jugador, carta):
        enfrentamiento = Enfrentamiento()
        enfrentamiento.ronda = self
        enfrentamiento.jugador_empezo_pos = list(self.jugadores.all()).index(jugador)
        enfrentamiento.save()
        enfrentamiento.agregar_carta(carta)

    def responder_canto(self, respuesta):
        ultimo_canto = list(self.canto_set.all())[-1]
        if respuesta == OPCIONES[QUIERO]:
            ultimo_canto.aceptar()
        else:
            ultimo_canto.rechazar()
        self.turno = ultimo_canto.pos_jugador_canto
#        self.opciones = ''
        self.save()

    def crear_canto(self, tipo, jugador):
        canto = Canto()
        canto.tipo = tipo
        canto.pts_en_juego = PTS_CANTO[tipo]
        canto.ronda = self
        canto.pos_jugador_canto = (list(self.jugadores.all())).index(jugador)
        canto.mano_pos = self.mano_pos
        canto.save()
        canto.jugadores = self.jugadores.all()
        canto.save()
        self.turno= (self.turno + 1) % len(self.jugadores.all())
        self.opciones = str(QUIERO)+str(NO_QUIERO)
        self.save()

    def calcular_puntos(self):
        # Una vez terminada la ronda se calculan los puntos de los equipos
        puntajes=[0,0]
        enfrentamientos_ganados=[0,0]
        for enfrentamiento in self.enfrentamiento_set.all():
        # Calcula cuantos enfrentamientos gano cada equipo
            ganador = enfrentamiento.ganador_pos
            if ganador >= 0:
                equipo_ganador =  list(self.jugadores.all())[ganador].equipo
                enfrentamientos_ganados[equipo_ganador] += 1
        if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
        # Si se empataron los tres enfrentamientos
            ganador = self.jugadores.all()[self.mano_pos].equipo
        else:
            ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
        puntajes[ganador] += 1
        canto = self.canto_set.filter(tipo=TRUCO)
        if canto:
            canto[0].equipo_ganador = ganador
            canto[0].save()
        for canto in self.canto_set.all():
            equipo_ganador = canto.equipo_ganador
            puntajes[equipo_ganador] += canto.pts_en_juego
        return puntajes

#FALTAN VER LOS CASOS DONDE HAY EMPATES!!!!
    def hay_ganador(self):
    # Devuelve verdadero si hay un ganador de la ronda
        result = False
        enfrentamientos_ganados = [0, 0]
        for enfrentamiento in self.enfrentamiento_set.all():
            ganador = enfrentamiento.ganador_pos
            if ganador >= 0:
                equipo_ganador = self.jugadores.all()[ganador].equipo
                enfrentamientos_ganados[equipo_ganador] += 1
        if len(self.enfrentamiento_set.all())==3:
            result = True
        elif (len(self.enfrentamiento_set.all())==2 and 
              enfrentamientos_ganados[0] != enfrentamientos_ganados[1]):
            result = True
        return result

    def tirar(self, jugador, carta):
        ultimo_enfrentamiento = list(self.enfrentamiento_set.all())[-1:]
        self.termino = self.hay_ganador()
        if self.termino:
            self.partida.crear_ronda()

        else:
            if ultimo_enfrentamiento and not ultimo_enfrentamiento[0].termino:
                ultimo_enfrentamiento = ultimo_enfrentamiento[0]
                ultimo_enfrentamiento.agregar_carta(carta)
                ganador = ultimo_enfrentamiento.get_ganador() 
                self.turno = ganador
                if list(self.enfrentamiento_set.all()).index(ultimo_enfrentamiento) == 0:
                    self.opciones += str(CANTAR_TRUCO)
                self.save()
            else:
                self.turno = (self.turno +1) % len(list(self.jugadores.all()))
                self.save()
                self.crear_enfrentamiento(jugador, carta)



class Canto(models.Model):
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    ronda = models.ForeignKey(Ronda, verbose_name= "ronda")
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    equipo_ganador = models.IntegerField(max_length=1, default=-1)
    pos_jugador_canto = models.IntegerField(max_length=1)
    puntos_ganador = models.IntegerField(max_length=2, default=0)

    def aceptar(self):
        self.pts_en_juego += 1
        self.save()
        if int(self.tipo) == ENVIDO:
            ganador = self.get_ganador()
            self.ronda.opciones = str(CANTAR_TRUCO)

    def rechazar(self):
        self.equipo_ganador = list(self.jugadores.all())[self.pos_jugador_canto].equipo
        self.save()

    def dist_mano(self, x):
        return (x + 1) % (self.ronda.mano_pos + 1)

    def get_ganador(self):
    # Calcula el ganador y los puntos del envido
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            puntos_jugadores.append(self.puntos_jugador(jugador))
        maximo_puntaje = max(puntos_jugadores)
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        distanciasamano = map(self.dist_mano,ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        ganador_pos = ganadores[minposfrom]
        self.equipo_ganador = jugadores[ganador_pos].equipo
        self.puntos_ganador = maximo_puntaje
        self.save()
        return (self.equipo_ganador, maximo_puntaje)

    def puntos_jugador(self, jugador):
    # Calcula los puntos de un jugador
        cartas = jugador.cartas.all()
        comb = list(combinations(cartas,2))
        return max(map(self.puntos_2_cartas,comb))

    def puntos_2_cartas(self,(carta1,carta2)):
        puntos=0
        if carta1.palo == carta2.palo:
            puntos = 20 + carta1.valor_envido + carta2.valor_envido
        else:
            puntos = max(carta1.valor_envido,carta2.valor_envido)
        return puntos




class Enfrentamiento(models.Model):
    ronda = models.ForeignKey(Ronda, verbose_name= "ronda")
    cartas = models.ManyToManyField(Carta, through='Tirada', verbose_name='cartas')
    jugador_empezo_pos = models.IntegerField(max_length=1)
    ganador_pos = models.IntegerField(max_length=1, default=-1)
    empate = models.BooleanField(default=False)
    termino = models.BooleanField(default=False)

    def get_ganador(self):
        self.termino = True ## por que true? cuando se deberia llamar a la funcion?
        carta_ganadora = min(self.cartas.all(), key= lambda c: c.valor_jerarquico)
        maximo_puntaje = carta_ganadora.valor_jerarquico
## ????
        ganadores = [i for i, j in enumerate(self.cartas.order_by("tirada__orden")) if
                     j.valor_jerarquico == maximo_puntaje]
        if len(ganadores) > 1:
            self.ganador_pos=-1
            self.empate = True
        else:
            ganador_pos_carta = list(self.cartas.all()).index(carta_ganadora)
            self.ganador_pos = (self.jugador_empezo_pos + ganador_pos_carta)%len(self.cartas.all())
        self.save()
        return self.ganador_pos

    def agregar_carta(self, carta):
        tirada = Tirada.objects.create(carta=carta, enfrentamiento=self, orden=len(self.cartas.all()))
        tirada.save()



class Tirada(models.Model):
    carta = models.ForeignKey(Carta)
    enfrentamiento = models.ForeignKey(Enfrentamiento)
    orden = models.IntegerField(max_length=0)
