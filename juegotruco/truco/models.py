import random
import heapq # Para encontrar los maximos dos elementos en calcular envido
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


class Envido(models.Model):
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')

    def get_ganador(self):
# MODULARIZAR! VER QUE PASA SI HAY DOS JUGADORES CON LOS MISMOS PUNTOS!
        puntos_jugadores = []
        for jugador in self.jugadores:
        # Calcular los puntos de cada jugador
            puntos = 0
            palo = 0
            cartas_mismo_palo = 0 # Cartas del mismo palo
            cartas_vistas = 0
            for carta in jugador.cartas:
                if cartas_vistas == 0:
                # Si es la primer carta
                    cartas_mismo_palo = 1
                    carta_en_vista = 1
                    palo = carta.palo
                    puntos = carta.valor_envido
                    puntos1 = carta.valor_envido # Por si son las tres iguales
                else:
                    if cartas_vistas == 1:
                    # Es la segunda carta
                        cartas_vistas = 2
                        puntos2 = carta.valor_envido # Por si son las tres iguales o si solo son iguales la segunda y tercera
                        palo2 = carta.palo # Por si solo la segunda y tercera son iguales
                        if carta.palo == palo:
                        # Si es del mismo palo
                            cartas_mismo_palo = 2
                            puntos += 20
                            puntos += puntos2
                    else:
                    # Es la tercer carta
                        puntos3 = carta.valor_envido
                        if cartas_mismo_palo == 2:
                            if carta.palo == palo:
                            # Las tres son del mismo palo
                                mayores_valores = heapq.nlargest(2, (puntos1, puntos2, puntos3))
                                puntos = 20 + mayores_valores[0] + mayores_valores[1]
                        else:
                            if carta.palo == palo:
                            # Si solo la primera y tercera son iguales
                                puntos += 20
                                puntos += puntos3
                            else:
                            # La primera no es igual a ninguna
                                if(carta.palo == palo2):
                                # Si la segunda y tercera son iguales
                                    puntos = 20 + puntos2 + puntos3
                                else:
                                # Las tres cartas son distintas
                                    puntos = max(puntos1, puntos2, puntos3)
            puntos_jugadores.append(puntos)
        return self.jugadores[puntos_jugadores.index(max(puntos_jugadores))]


