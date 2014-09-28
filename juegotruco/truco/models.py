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
    cartas = Carta.objects.all() 

    def get_n_cartas(self, cant_cartas):
        return random.sample(self.cartas, cant_cartas)



class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)
    cartas = models.ManyToManyField(Carta, related_name='cartas')
    cartas_disponibles = models.ManyToManyField(Carta, related_name='cartas_disponibles')

    def asignar_cartas(self, cartas):
        self.cartas = cartas
        self.cartas_disponibles = cartas
        self.save()

    def __str__(self):
        return self.nombre


class Lobby:

    def get_lista_partidas(self):
        lista_partidas = Partida.objects.filter(estado=EN_ESPERA)
        return (lista_partidas)

    def crear_partida(self, user, nombre, puntos_objetivo, password):
        partida = Partida(nombre=nombre, puntos_objetivo=puntos_objetivo, password=password, mano_pos=0)
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
    puntaje_truco = []
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
            if len(self.jugadores.all()) >= self.cantidad_jugadores:
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
        ronda.save()
        ronda.mano_pos = self.mano_pos
        ronda.jugadores = self.jugadores.all()
        ronda.repartir()
        ronda.save()
        self.mano_pos = (self.mano_pos +1)%self.cantidad_jugadores
        return ronda

    def actualizar_puntajes():
        ultima_ronda = list(self.ronda_set.all())[-1]
        self.puntajes = map(add,self.puntajes,ultima_ronda.calcular_puntos())
        if len([i for i in self.puntajes if i > puntos_objetivo])>0:
            self.estado = TERMINADA

    def tirar(self,jugador,carta):
        ronda_actual = list(self.ronda_set.all())[-1]
        ronda_actual.tirar(jugador,carta)
        if ronda_actual.termino:
            self.actualizar_puntajes()
        return self.termino()


class Ronda(models.Model):
    # Estado inical de una ronda
    partida = models.ForeignKey(Partida, verbose_name= "partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo() # No deberiamos crear un mazo siempre
    mano_pos = models.IntegerField(max_length=1)
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

    def crear_enfrentamiento(self,jugador,carta):
        enfrentamiento = Enfrentamiento()
        enfrentamiento.ronda = self
        enfrentamient.jugador_pos = list(self.jugadores.all()).index(jugador)
        enfrentamiento.cartas.add(carta)

    def crear_canto(self, tipo,equipo):
        canto = Canto(tipo=tipo, pts_en_juego = PTS_CANTO[tipo])
        canto.ronda = self
        canto.equipo_canto = equipo
        canto.mano_pos = self.mano_pos
        canto.save()
        canto.jugadores = self.jugadores.all()
        canto.save()

    def calcular_puntos(self):
        puntajes=[]
        enfrentamientos_ganados=[]
        for canto in self.canto_set.all():
            equipo_ganador = canto.get_ganador()
            puntajes[equipo_ganador] += canto.pts_en_juego
        for enfrentamiento in self.enfrentamiento_set.all():
            pos_ganador = enfrentamiento.ganador_pos
            if pos_ganador > 0:
                equipo_ganador = self.jugadores.all()[pos_ganador].equipo
                enfrentamientos_ganados[equipo_ganador] += 1
        if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
            ganador = self.jugadores.all()[mano_pos].equipo
        else:
            ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
        puntajes[ganador]+=1
        return puntajes

    def tirar(jugador,carta):
        ultimo_enfrentamiento = list(self.enfrentamiento_set.all())[-1]
        if not ultimo_enfrentamiento.terimo:
            ultimo_enfrentamiento.agregar_carta(carta)
            ultimo_enfrentamiento.get_ganador()
            self.turno = ultimo_enfrentamiento.get_ganador()
        else:
            self.crear_enfrentamiento(jugador,carta)



class Canto(models.Model):
    ronda = models.ForeignKey(Ronda, verbose_name= "ronda")
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    equipo_canto = models.IntegerField()
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mano_pos = models.IntegerField(max_length=1)

    def aceptar(self):
        self.pts_en_juego += 1;

    def rechazar(self):
        # Como ya se pasa como parametro no hace nada
        pass

    def dist_mano(self,x):
        return (x+1) % (self.mano_pos+1)

    def get_ganador(self):
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            puntos_jugadores.append(self.puntos_jugador(jugador))
        maximo_puntaje = max(puntos_jugadores)
        print maximo_puntaje
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        print ganadores
        distanciasamano = map(self.dist_mano,ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        ganador_pos = ganadores[minposfrom]
        return jugadores[ganador_pos].equipo

    def puntos_jugador(self,jugador):
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
    cartas = models.ManyToManyField(Carta, verbose_name='cartas')
    jugador_canto_pos = models.IntegerField(max_length=1)
    ganador_pos = models.IntegerField(max_length=1)
    empate = models.BooleanField(default=False)
    termino = models.BooleanField(default=False)

    def get_ganador(self):
        carta_ganadora = max(self.cartas.all(),key= lambda c: c.valor_jerarquico)
        ganadores = [i for i, j in enumerate(self.cartas.all()) if
                     j.valor_jerarquico == maximo_puntaje]
        if len(ganadores) > 1:
            self.ganador_pos=-1
            self.empate = True
        ganador_pos_carta = list(self.cartas.all()).index(carta_ganadora)
        self.ganador_pos = (jugador_canto_pos + ganador_pos_carta)%len(self.cartas.all())
        return self.ganador_pos

    def agregar_carta(self,carta):
        cartas.add(carta)
