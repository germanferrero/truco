from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse

class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)

class Lobby:

    def get_lista_partidas(self):
        lista_partidas = Partida.objects.filter(estado=EN_ESPERA)
        return (lista_partidas)

    def crear_partida(self, user, puntos_objetivo, password):
        partida = Partida(puntos_objetivo=puntos_objetivo, password=password)
        partida.save()
        partida.agregar_jugador(user)
        partida.set_mano(jugador)

    def unirse_partida(self, jugador,partida):
        result=0
        if partida.estado == EN_ESPERA:
            partida.agregar_jugador(jugador)
        else:
            result=-1
        return result

class Partida(models.Model):
    #falta puntaje
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano = models.IntegerField(default=0)
    cantidad_jugadores = models.IntegerField(default=2)

    def agregar_jugador(self,user):
            jugador = Jugador(nombre=username,equipo=list(self.jugadores).length%2)
            jugador.user = user
            jugador.save()
            self.jugadores.add(jugador)
            self.save()
            if list(self.jugadores).length == self.cantidad_jugadores:
                self.estado = EN_CURSO


    def set_mano(self,jugador):
        self.mano = jugador.id
        self.save()

    def get_absolute_url(self):
        return reverse('people.views.details', args=[str(self.id)])
