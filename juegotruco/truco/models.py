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
            return list(Carta.objects.order_by('?')[:cant_cartas])



class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)
    cartas = models.ManyToManyField(Carta, related_name='cartas')
    cartas_disponibles = models.ManyToManyField(Carta, related_name='cartas_disponibles')
    cartas_jugadas = models.ManyToManyField(Carta, related_name='cartas_jugadas')

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
        #Agrega jugadores a la partida, uno a cada equipo por orden de ingreso.
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

### Actualmente en desuso ###
#    def get_absolute_url(self):
#        return HttpResponseRedirect(reverse('partida'))

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
        # En la proxima ronda, sera mano el jugador de la "derecha".
        self.mano_pos = (self.mano_pos + 1)%self.cantidad_jugadores
        self.save()
        return ronda

    def actualizar_puntajes(self):
        # Esta funcion se invoca al terminar una ronda.
        ultima_ronda = list(self.ronda_set.all())[-1]
        puntos = ultima_ronda.calcular_puntos()
        self.puntos_e1 += puntos[0]
        self.puntos_e2 += puntos[1]
        if (self.puntos_e1 >= self.puntos_objetivo
            or self.puntos_e2 >= self.puntos_objetivo):
            #Algun equipo logro los puntos objetivo, se termina la partida
            self.estado = FINALIZADA
        else:
            self.crear_ronda()
        self.save()

    def tirar(self,jugador,carta):
        ronda_actual = list(self.ronda_set.all())[-1]
        ronda_actual.tirar(jugador,carta)
        jugador.cartas_disponibles.remove(carta)
        jugador.cartas_jugadas.add(carta)
        if ronda_actual.termino:
            self.actualizar_puntajes()
        return self.estado



class Ronda(models.Model):
    # Estado inical de una ronda
    partida = models.ForeignKey(Partida, verbose_name= "partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo()
    mano_pos = models.IntegerField(max_length=1,default=0)
    turno = models.IntegerField(max_length=1, default=0)
    termino = models.BooleanField(default=False)
    opciones = models.CharField(max_length=10, default= str(CANTAR_ENVIDO))

    def repartir(self):
        # Toma cartas al azar del mazo y las asigna a los jugadores
        cartas_a_repartir = self.mazo.get_n_cartas(len(self.jugadores.all())*CARTAS_JUGADOR)
        desde = 0
        for jugador in self.jugadores.all():
            hasta = desde + 3
            jugador.asignar_cartas(cartas_a_repartir[desde:hasta])
            desde = desde + 3

    def crear_enfrentamiento(self, jugador, carta):
        # Crea un enfrentamiento con la carta que le dio inicio
        enfrentamiento = Enfrentamiento()
        enfrentamiento.ronda = self
        enfrentamiento.jugador_empezo_pos = list(self.jugadores.all()).index(jugador)
        enfrentamiento.save()
        self.save()
        enfrentamiento.agregar_carta(carta)

    def responder_canto(self, respuesta):
        # Toma la respuesta a un canto
        ultimo_canto = list(self.canto_set.all())[-1]
        if respuesta == OPCIONES[QUIERO]:
            if ultimo_canto.tipo == ENVIDO:
                # En caso de ser un envido, hay que calcular el ganador
                ultimo_canto.envido.aceptar()
                ultimo_canto.envido.get_ganador()
            else:
                ultimo_canto.aceptar()
        else:
            ultimo_canto.rechazar()
        # Se asigna el turno al jugador que realizo el canto
        self.turno = ultimo_canto.pos_jugador_canto
        # Las opciones se limpian, si se acepto un envido estamos en el primer
        # enfrentamiento, luego la opcion truco no debe estar en opciones aun.
        # Claramente, tampoco deben estar ya las opciones QUIERO y NO QUIERO
        self.opciones = ''
        self.save()

    def crear_canto(self, tipo, jugador):
        if tipo == ENVIDO:
            canto = Envido(mano_pos=self.mano_pos)
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
        # Se asigna el turno al jugador de la "derecha" para que responda
        self.turno= (self.turno+1)%len(self.jugadores.all())
        # Se agregan las opciones para la respuesta del adversario
        self.opciones = str(QUIERO)+str(NO_QUIERO)
        self.save()

    def calcular_puntos(self):
        # Una vez terminada la ronda se calculan los puntos de los equipos
        puntajes=[0,0]
        enfrentamientos_ganados=[0,0]
        # Verificamos si el truco estaba cantado
        canto = self.canto_set.filter(tipo=TRUCO)
        if canto & canto[0].equipo_ganador >=0:
            # Truco cantado y rechazado, por lo tanto ya hay un ganador
            puntajes[canto[0].equipo_ganador] += 1
        else:
            # Hay que calcular el ganador de los enfrentamientos
            for enfrentamiento in self.enfrentamiento_set.all():
                # Calcula cuantos enfrentamientos gano cada equipo
                ganador = enfrentamiento.ganador_pos
                if ganador >= 0:
                    # No hubo un empate
                    equipo_ganador =  list(self.jugadores.all())[ganador].equipo
                    enfrentamientos_ganados[equipo_ganador] += 1
            if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
                # Si se empataron los tres enfrentamientos
                ganador = self.jugadores.all()[mano_pos].equipo
            else:
                # Ganador es el equipo con mas enfrentamientos ganados
                ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
                puntajes[ganador] += 1
            if canto:
                # El Truco se canto y acepto, luego hay que definir el ganador
                canto[0].equipo_ganador = ganador
                canto[0].save()
        for canto in self.canto_set.all():
            # Asignamos los puntos correspondientes a los cantos
            equipo_ganador = canto.equipo_ganador
            puntajes[equipo_ganador] += canto.pts_en_juego
        return puntajes

    def hay_ganador(self):
        # Devuelve verdadero si hay un ganador de la ronda
        result = False
        if len(self.enfrentamiento_set.all()) == 3:
            # Se jugadon los 3 enfrentamientos
            result = True
        elif len(self.enfrentamiento_set.all()) == 2:
            # Se jugaron 2 enfrentamientos
            enfrentamientos_ganados = [0,0]
            for enfrentamiento in self.enfrentamiento_set.all():
                ganador = enfrentamiento.ganador_pos
                if ganador >= 0:
                    equipo_ganador = list(self.jugadores.all())[ganador].equipo
                    enfrentamientos_ganados[equipo_ganador] += 1
            if enfrentamientos_ganados[0] != enfrentamientos_ganados[1]:
                # Uno de los dos gano mas que el otro, luego gano la ronda
                result = True
        return result

    def tirar(self, jugador, carta):
        # Tirar una carta
        ultimo_enfrentamiento = list(self.enfrentamiento_set.all())[-1:]
        if ultimo_enfrentamiento and not ultimo_enfrentamiento[0].termino:
            # Existe un enfrentamiento y este no termino
            ultimo_enfrentamiento[0].agregar_carta(carta)
            # Calculamos el ganador para darle el turno
            ganador = ultimo_enfrentamiento[0].get_ganador()
            if ganador >= 0:
                # No hubo empate
                self.turno = ganador
            else:
                self.turno = self.mano_pos
            # Verificamos si hay un ganador de la ronda
            self.termino = self.hay_ganador()
            if list(self.enfrentamiento_set.all()).index(ultimo_enfrentamiento[0]) == 0:
                # Ademas si hemos finalizado el primer enfrentamiento, agregamos
                # la opcion de cantar "Truco".
                self.opciones += str(CANTAR_TRUCO)
            self.save()
        else:
            # La carta tirada forma parte de un nuevo enfrentamiento
            self.crear_enfrentamiento(jugador, carta)
            # Se asigna el turno al jugador de la "derecha"
            self.turno = (self.turno+1)%len(self.jugadores.all())
            self.save()




class Canto(models.Model):
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    ronda = models.ForeignKey(Ronda, verbose_name= "ronda")
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    equipo_ganador = models.IntegerField(max_length=1, default =-1)
    pos_jugador_canto = models.IntegerField(max_length=1)

    def aceptar(self):
        self.pts_en_juego += 1
        self.save()

    def rechazar(self):
        self.equipo_ganador = list(self.jugadores.all())[self.pos_jugador_canto].equipo
        self.save()

class Envido(Canto):
    mano_pos = models.IntegerField(max_length=1)

    def dist_mano(self, x):
        # Dada una posicion de un jugador, devuelve su distancia al jugador mano
        return (x + 1) % (self.mano_pos + 1)

    def get_ganador(self):
        # Calcula el ganador y los puntos del envido
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            # Agrego a la lista los puntos de los jugadores
            puntos_jugadores.append(self.puntos_jugador(jugador))
        maximo_puntaje = max(puntos_jugadores)
        # ganadores son aquellos que tienen el maximo_puntaje
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        # Calculamos la distancia de un jugador al mano pues esto le da prioridad
        distanciasamano = map(self.dist_mano,ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        # El jugador ganador es el mano de los demas ganadores
        ganador_pos = ganadores[minposfrom]
        # El equipo ganador es el equipo del jugador ganador
        self.equipo_ganador = jugadores[ganador_pos].equipo
        self.save()
        return (self.equipo_ganador, maximo_puntaje)

    def puntos_jugador(self, jugador):
        # Calcula los puntos de un jugador
        cartas = jugador.cartas.all()
        # Todas las combinaciones de sus cartas posibles
        comb = list(combinations(cartas,2))
        # Maximo puntaje de una combinacion
        return max(map(self.puntos_2_cartas,comb))

    def puntos_2_cartas(self,(carta1,carta2)):
        # Dada dos cartas devuelve el puntaje que suman entre ellas.
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
    ganador_pos = models.IntegerField(max_length=1, default=-1)
    termino = models.BooleanField(default=False)

    def get_ganador(self):
        # Esta funcion es invocada al finalizar un enfrentamiento
        # y devuelve el ganador del mismo, o -1 es caso de empate
        self.termino = True
        # De las cartas del enfrentamiento obtiene la de mayor (min->mayor) valor jerarquico
        carta_puntaje_ganador = min(self.cartas.all(), key= lambda c: c.valor_jerarquico)
        maximo_puntaje = carta_puntaje_ganador.valor_jerarquico
        # Indices de las cartas del enfrentamiento que comparten el maximo_puntaje
        cartas_ganadoras = [i for i, j in enumerate(self.cartas.all()) if
                            j.valor_jerarquico == maximo_puntaje]
        if len(cartas_ganadoras) > 1:
            # Hay un empate, pues hay 2 cartas con el mismo valor jerarquico
            # En proximas iteraciones hay que diferenciar a que equipo pertenecen las cartas
            self.ganador_pos=-1
        else:
            # Ver documentacion: "Problema de orden en que se jugaron las cartas"
            # Orden en que fue jugada la carta ganadora. Ej: "la segunda carta"
            carta_ganadora_pos = list(self.cartas.order_by("tirada__orden")).index(carta_ganadora)
            # Calculamos a quien corresponde, segun quien empezo y la carta que gano
            self.ganador_pos = (self.jugador_empezo_pos + carta_ganadora_pos)%len(self.cartas.all())
        self.save()
        return self.ganador_pos

    def agregar_carta(self, carta):
        # Agregamos una carta al enfrentamiento guardando el orden en que se lanzo
        # Ejemplo: "primera carta del enfrentamiento" o "segunda carta del enfrentamiento"
        tirada= Tirada.objects.create(carta=carta, enfrentamiento=self, orden=len(self.cartas.all()))
        tirada.save()

class Tirada(models.Model):
    carta = models.ForeignKey(Carta)
    enfrentamiento = models.ForeignKey(Enfrentamiento)
    orden = models.IntegerField(max_length=0)
