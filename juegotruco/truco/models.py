import random
from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from itertools import combinations
from operator import itemgetter


class Carta(models.Model):
    nombre = models.CharField(max_length=32)
    valor_jerarquico = models.IntegerField(max_length=2)
    valor_envido = models.IntegerField(max_length=1)
    palo = models.IntegerField(max_length=1)
# Agregar ImageField. Hay que volver a crear los objetos Carta
#    imagen = models.ImageField(upload_to='Carta', height_field=None, width_field=None)

    def __unicode__(self):
        return self.nombre



class Mazo():
    cartas = Carta.objects.all() 

    def get_n_cartas(self, cant_cartas):
        return random.sample(self.cartas, cant_cartas)



class Enfrentamiento(models.Model):
    cartas = models.ManyToManyField(Carta, verbose_name='cartas')
    id_jugador_empezo = models.IntegerField(max_length=1)

    def get_ganador(self):
        pass

    def agregar_carta(self):
        pass



class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)
    cartas = models.ManyToManyField(Carta, verbose_name='cartas')

    def asignar_cartas(self, cartas):
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
        partida.set_mano(jugador)
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
    puntaje_truco = []
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano = models.ForeignKey(Jugador, related_name='mano')
    cantidad_jugadores = models.IntegerField(default=2)

    def agregar_jugador(self,user):
            jugador = Jugador(nombre=user.username,equipo=len(self.jugadores.all())%2)
            jugador.user = user
            jugador.save()
            self.jugadores.add(jugador)
            self.save()
            if len(self.jugadores.all()) >= self.cantidad_jugadores:
                self.estado = EN_CURSO
                self.save()
            return jugador

    def set_mano(self,jugador):
        self.mano = jugador
        self.save()

    def get_absolute_url(self):
        return HttpResponseRedirect(reverse('partida'))

    def __unicode__(self):
        return self.nombre

    def crear_ronda(self):
        ronda = Ronda()
        ronda.mano = self.mano
        ronda.save()
        ronda.jugadores = self.jugadores.all()
        ronda.repartir()
        ronda.save()
        return ronda


class Canto(models.Model):
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    id_jugador_canto = models.IntegerField()
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mano = models.ForeignKey(Jugador, related_name='mano canto')

    def aceptar(self):
        self.pts_en_juego = 2;
#        COMO COMPARAR?
#        if (str(self.nombre) = "Envido"):
#            envido = Envido(self.jugadores)
#            self.ganador = envido.get_ganador()

    def rechazar(self):
        # Como ya se pasa como parametro no hace nada
        pass


    def dist_mano(self,x):
        mano_pos = list(self.jugadores.all()).index(self.mano)
        return (x+1) % (mano_pos+1)

    def get_ganador(self):
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            puntos_jugadores.append(self.puntos_jugador(jugador.cartas.all()))
        maximo_puntaje = max(puntos_jugadores)
        print puntos_jugadores
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        print "ganadores"
        print ganadores
        distanciasamano = map(self.dist_mano,ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        ganador_pos = ganadores[minposfrom]
        return jugadores[ganador_pos]

    def puntos_jugador(self,cartas):
        comb = list(combinations(cartas,2))
        return max(map(self.puntos_2_cartas,comb))

    def puntos_2_cartas(self,(carta1,carta2)):
        puntos=0
        if carta1.palo == carta2.palo:
            puntos = 20 + carta1.valor_envido + carta2.valor_envido
        else:
            puntos = max(carta1.valor_envido,carta2.valor_envido)
        return puntos


class Ronda(models.Model):
    # Estado inical de una ronda
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    cantos = models.ManyToManyField(Canto, verbose_name='cantos')
    enfrentamientos = models.ManyToManyField(Enfrentamiento, verbose_name='enfrentamientos')
    mazo = Mazo() # No deberiamos crear un mazo siempre
    mano = models.ForeignKey(Jugador, related_name='mano ronda')
    turno = models.IntegerField(max_length=1, default=0)
    terminada = False
    id_enfrentamiento_actual = models.IntegerField(default=0)
    id_canto_actual = models.IntegerField(default=0)

    def repartir(self):
        cartas_a_repartir = self.mazo.get_n_cartas(len(self.jugadores.all())*CARTAS_JUGADOR)
        desde = 0
        for j in self.jugadores.all():
            hasta = desde + 3
            j.asignar_cartas(cartas_a_repartir[desde:hasta])
            desde = desde + 3

    def crear_enfrentamiento(self):
        # MAL! al enfrentamiento no se le pasan todas las cartas del mazo! Ademas que es Mazo?
        self.enfrentamiento = Enfrentamiento(id_jugador_empezo=self.mano, cartas=Mazo.cartas)

    def crear_canto(self, tipo,jugador_id):
        if tipo == ENVIDO:
            canto = Envido(tipo=ENVIDO)
        else:
            canto = Canto(tipo=tipo)
        canto.id_jugador_canto = jugador_id
        canto.mano = self.mano
        canto.save()
        canto.jugadores = self.jugadores.all()
        canto.save()
        self.cantos.add(canto)



class Envido(Canto):

    def dist_mano(x):
        mano_pos = list(self.jugadores.all()).index(self.mano)
        return (x+1) % (mano_pos+1)

    def get_ganador(self):
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            puntos_jugadores.append(puntos_jugador(jugador.cartas.all()))
        maximo_puntaje = max(puntos_jugadores)
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        ganador_pos = min(map(dist_mano,ganadores))
        return jugadores[ganador_pos]

    def puntos_jugador(cartas):
        comb = list(combinations(cartas,2))
        return max(map(puntos_2_cartas,comb))

    def puntos_2_cartas((carta1,carta2)):
        puntos=0
        if carta1.palo == carta2.palo:
            puntos = 20 + carta1.valor_envido + carta2.valor_envido
        else:
            puntos = max(carta1.valor_envido,carta2.valor_envido)
        return puntos
