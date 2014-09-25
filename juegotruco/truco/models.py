from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect

class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)

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
    #falta puntaje
    nombre = models.CharField(max_length=32)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
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
            if len(self.jugadores.all()) == self.cantidad_jugadores:
                self.estado = EN_CURSO
            return jugador

    def set_mano(self,jugador):
        self.mano = jugador.id
        self.save()

    def get_absolute_url(self):
        return HttpResponseRedirect(reverse('partida'))

    def __unicode__(self):
        return self.nombre