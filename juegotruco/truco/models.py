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
        ronda.mano_pos = self.mano_pos
        ronda.turno = self.mano_pos
        ronda.save()
        ronda.jugadores = self.jugadores.all()
        ronda.repartir()
        ronda.save()
        self.mano_pos = (self.mano_pos +1)%self.cantidad_jugadores
        return ronda

    def actualizar_puntajes(self):
        ultima_ronda = list(self.ronda_set.all())[-1]
        puntos = ultima_ronda.calcular_puntos()
        self.puntos_e1 = self.puntos_e1 + puntos[0]
        self.puntos_e2 = self.puntos_e2 + puntos[1]
        if self.puntos_e1 >= self.puntos_objetivo or self.puntos_e2 >= self.puntos_objetivo:
            self.estado = FINALIZADA
        else:
            self.crear_ronda()
        self.save()

    def tirar(self,jugador,carta):
        ronda_actual = list(self.ronda_set.all())[-1]
        ronda_actual.tirar(jugador,carta)
        if ronda_actual.termino:
            self.actualizar_puntajes()
        jugador.cartas_disponibles.remove(carta)
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
    opciones = models.CharField(max_length=10, default= str(CANTAR_ENVIDO))

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
        enfrentamiento.jugador_empezo_pos = list(self.jugadores.all()).index(jugador)
        enfrentamiento.save()
        enfrentamiento.agregar_carta(carta)

    def responder_canto(self,respuesta):
        ultimo_canto = list(self.canto_set.all())[-1]
        if respuesta == QUIERO:
            ultimo_canto.aceptar()
        else:
            ultimo_canto.rechazar()
        self.turno = ultimo_canto.pos_jugador_canto
        self.opciones = ''
        self.save()

    def crear_canto(self, tipo,jugador):
        if tipo == ENVIDO:
            canto = Envido()
        else:
            canto = Canto()
        canto.tipo = tipo
        canto.pts_en_juego = PTS_CANTO[tipo]
        canto.ronda = self
        canto.pos_jugador_canto = (list(self.jugadores.all())).index(jugador)
        canto.mano_pos = self.mano_pos
        canto.save()
        canto.jugadores = self.jugadores.all()
        canto.save()
        self.turno= (self.turno+1)%len(self.jugadores.all())
        self.opciones = str(QUIERO)+str(NO_QUIERO)
        self.save()

    def calcular_puntos(self):
        puntajes=[0,0]
        enfrentamientos_ganados=[0,0]
        for enfrentamiento in self.enfrentamiento_set.all():
            ganador = enfrentamiento.ganador_pos
            if ganador >= 0:
                equipo_ganador = self.jugadores.all()[ganador].equipo
                enfrentamientos_ganados[equipo_ganador] += 1
        if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
            ganador = self.jugadores.all()[mano_pos].equipo
        else:
            ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
        puntajes[ganador]+=1
        canto=self.canto_set.filter(tipo=TRUCO)
        if canto:
            canto[0].equipo_ganador = ganador
            canto[0].save()
        for canto in self.canto_set.all():
            equipo_ganador = canto.equipo_ganador
            puntajes[equipo_ganador] += canto.pts_en_juego
        return puntajes

    def hay_ganador(self):
        result = False
        enfrentamientos_ganados = [0,0]
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

    def tirar(self,jugador,carta):
        ultimo_enfrentamiento = list(self.enfrentamiento_set.all())[-1:]
        print "ultimo_enfrentamiento", ultimo_enfrentamiento
        if ultimo_enfrentamiento and not ultimo_enfrentamiento[0].termino:
            print "no se termino el enfrentamiento"
            ultimo_enfrentamiento[0].agregar_carta(carta)
            ganador = ultimo_enfrentamiento[0].get_ganador()
            self.turno = ganador
            self.termino = self.hay_ganador()
            if list(self.enfrentamiento_set.all()).index(ultimo_enfrentamiento[0]) == 0:
                self.opciones += str(CANTAR_TRUCO)
            self.save()
        else:
            self.crear_enfrentamiento(jugador,carta)




class Canto(models.Model):
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    ronda = models.ForeignKey(Ronda, verbose_name= "ronda")
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    equipo_ganador = models.IntegerField(max_length=1)
    pos_jugador_canto = models.IntegerField(max_length=1)

    def aceptar(self):
        self.pts_en_juego += 1
        self.save()

    def rechazar(self):
        self.equipo_ganador = self.jugadores.all()[self.pos_jugador_canto].equipo
        self.save()
        # Como ya se pasa como parametro no hace nada
        pass

class Envido(Canto):
    mano_pos = models.IntegerField(max_length=1)

    def dist_mano(self,x):
        return (x+1) % (self.mano_pos+1)

    def get_ganador(self):
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
        self.save()
        return (self.equipo_ganador, maximo_puntaje)

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
    cartas = models.ManyToManyField(Carta, through='Tirada',verbose_name='cartas')
    jugador_empezo_pos = models.IntegerField(max_length=1)
    ganador_pos = models.IntegerField(max_length=1)
    empate = models.BooleanField(default=False)
    termino = models.BooleanField(default=False)

    def get_ganador(self):
        self.termino = True
        carta_ganadora = min(self.cartas.all(),key= lambda c: c.valor_jerarquico)
        maximo_puntaje = carta_ganadora.valor_jerarquico
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

    def agregar_carta(self,carta):
        tirada= Tirada.objects.create(carta=carta,enfrentamiento=self,orden=len(self.cartas.all()))
        tirada.save()

class Tirada(models.Model):
    carta = models.ForeignKey(Carta)
    enfrentamiento = models.ForeignKey(Enfrentamiento)
    orden = models.IntegerField(max_length=0)
