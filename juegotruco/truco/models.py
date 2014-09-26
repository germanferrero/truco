import random
from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect


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
        return random.sample(cartas, cant_cartas)



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
        if partida.estado == EN_ESPERA:
            partida.agregar_jugador(user)
        else:
            result=-1
        return result



class Partida(models.Model):
    nombre = models.CharField(max_length=32)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntaje_truco = []
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano = models.IntegerField(default=0)
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
        self.mano = jugador.id
        self.save()

    def get_absolute_url(self):
        return HttpResponseRedirect(reverse('partida'))

    def __unicode__(self):
        return self.nombre

    def crear_ronda(self):
        ronda = Ronda(jugadores=self.jugadores, mano=self.mano)
        return ronda



class Ronda(models.Model):
    # Estado inical de una ronda
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    cantos = []
    enfrentamientos = []
    mazo = Mazo() # No deberiamos crear un mazo siempre
    mano = models.IntegerField(default=0)
    turno = mano #mano?
    terminada = False
    id_enfrentamiento_actual = models.IntegerField(default=0)
    id_canto_actual = models.IntegerField(default=0)

    def repartir(self):
        cartas_a_repartir = Mazo.get_n_cartas(len(self.jugadores)*CARTAS_JUGADOR)
        for j in self.jugadores:
            desde = 0
            hasta = desde + 3
            j.asignar_cartas(cartas_a_repartir[desde:hasta])
            desde = desde + 3

    def crear_enfrentamiento(self):
        # MAL! al enfrentamiento no se le pasan todas las cartas del mazo! Ademas que es Mazo?
        self.enfrentamiento = Enfrentamiento(id_jugador_empezo=self.mano, cartas=Mazo.cartas)

    def crear_canto(self, nombre):
        self.cantos = self.cantos.append(Canto(self, nombre=nombre))



class Canto(models.Model):
    nombre = models.CharField(max_length=6)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    id_jugador_canto = models.IntegerField()
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    #??> Pasar como parametro el jugador que canto
    ganador = Jugador

    def aceptar(self):
        self.pts_en_juego = 2;
#        COMO COMPARAR?
#        if (str(self.nombre) = "Envido"):
#            envido = Envido(self.jugadores)
#            self.ganador = envido.get_ganador()

    def rechazar(self):
        # Como ya se pasa como parametro no hace nada
        pass

    def get_pts_en_juego(self):
        return self.pts_en_juego


