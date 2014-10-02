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

    """
    Devuelve n de las cartas de la base de datos sin repetir.
    """
    def get_n_cartas(self, cant_cartas):
            return list(Carta.objects.order_by('?')[:cant_cartas])


class Jugador(models.Model):
    user = models.ForeignKey(User, verbose_name='usuario')
    nombre = models.CharField(max_length=32)
    equipo = models.IntegerField(max_length=1)
    cartas = models.ManyToManyField(Carta, related_name='cartas')
    cartas_disponibles = models.ManyToManyField(Carta, related_name='cartas_disponibles')
    cartas_jugadas = models.ManyToManyField(Carta, related_name='cartas_jugadas')

    """
    Asigna a cada jugador las cartas que se pasan como una lista de instancias de Carta.
    """
    def asignar_cartas(self, cartas):
        self.cartas = cartas
        self.cartas_disponibles = cartas
        self.cartas_jugadas = []
        self.save()

    """
    Devuelve las cartas de un jugador.
    """
    def get_cartas_diponibles(self):
        return list(self.cartas_disponibles.all())

    """
    Devuelve las cartas que el jugador ya tiro.
    """
    def get_cartas_jugadas(self):
        return list(self.cartas_jugadas.all())

    def __str__(self):
        return self.nombre


class Lobby:

    def get_lista_partidas(self):
        lista_partidas = Partida.objects.filter(estado=EN_ESPERA)
        return (lista_partidas)

    """
    Crea una nueva partida y une al usuario a la misma.
    """
    def crear_partida(self, user, nombre, puntos_objetivo, password):
        partida = Partida(nombre=nombre, puntos_objetivo=puntos_objetivo, password=password)
        partida.save()
        partida.agregar_jugador(user)
        return partida

    """
    Crea un jugador perteneciente a un usuario y lo pone en la partida.
    Devuelve 0 en caso de exito, -1 en caso contrario.
    """
    def unirse_partida(self, user, partida):
        result = 0
        for j in partida.jugadores.all():
            # Verifica que el usuario no este ya en la partida
            if j.user.id == user.id:
                result = -1
        if result == 0:
            partida.agregar_jugador(user)
        return result


class Partida(models.Model):
    nombre = models.CharField(max_length=32)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntos_e1 = models.IntegerField(max_length=2, default=0)
    puntos_e2 = models.IntegerField(max_length=2, default=0)
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano_pos = models.IntegerField(max_length=1, default=0)
    cantidad_jugadores = models.IntegerField(default=2)

    """
    Obtiene una partida segun su id.
    Si no existe devuelve None.
    """
    @classmethod
    def get(self, id):
        try:
            partida = Partida.objects.get(id=id)
        except:
            partida = None
        return partida

    """
    Devuelve true si una partida esta lista para empezar una nueva ronda.
    Esto es, si no se llego a los puntos objetivo de la partida,los jugadores
    estan listos y no hay una ronda en curso.
    """
    def is_ready(self):
        # Devuelve true si una partida esta lista para empezar nueva ronda
        rondas_terminadas = all([ronda.hay_ganador() for ronda in list(self.ronda_set.all())[-1:]])
        jugadores_listos = len(self.jugadores.all()) == self.cantidad_jugadores
        ganador = self.get_ganador()
        return rondas_terminadas and jugadores_listos and ganador < 0

    """
    Devuelve la ronda actual si existe, None en caso contrario.
    """
    def get_ronda_actual(self):
        #Devuelve la ronda acutal
        try:
            ronda = list(self.ronda_set.all())[-1]
        except:
            ronda = None
        return ronda

    """
    Devuelve un mensaje si hay un equipo ganador, si no devuelve un string vacio.
    """
    def get_mensaje_ganador(self, user):
        result = ''
        jugador = self.find_jugador(user)
        equipo = jugador.equipo
        ganador = self.get_ganador()
        if ganador >= 0:
            if ganador == equipo:
                result = 'Has ganado'
            else:
                result = 'Has perdido'
        return result

    """
    Devuelve el jugador de un usuario en la partida,
    si no posee un jugador devuelve None.
    """

    def find_jugador(self, user):
        try:
            jugador = self.jugadores.get(user=user)
        except:
            jugador = None
        return jugador

    """
    Devuelve el equipo ganador de la partida.
    """
    def get_ganador(self):
        result = -1
        if(self.puntos_e1 >= self.puntos_objetivo):
            result = 0
        elif(self.puntos_e2 >= self.puntos_objetivo):
            result = 1
        return result

    """
    Devuelve el puntaje de la partida, ordenado para user.
    """
    def get_puntajes(self, user):
        jugador = self.jugadores.get(user=user)
        if jugador.equipo == 0:
            result = [self.puntos_e1, self.puntos_e2]
        else:
            result = [self.puntos_e2, self.puntos_e1]
        return result

    """
    Devuelve verdadero si se pueden agregar mas jugadores a la partida.
    """
    def acepta_jugadores(self):
        result = False
        if self.estado == EN_ESPERA:
            result = True
        return result

    """
    Agrega jugadores a la partida, uno a cada equipo por orden de ingreso.
    """
    def agregar_jugador(self, user):
        jugador = Jugador(nombre=user.username, equipo=len(self.jugadores.all()) % 2)
        jugador.user = user
        jugador.save()
        self.jugadores.add(jugador)
        self.save()

    """
    Actualiza el estado de la partida.
    Si la partida tiene la cantidad de jugadores que tiene que tener, establece
    el estado en "en curso".
    Si la partida se termino, este metodo no se llama, por lo que no contempla
    ese caso.
    """
    def actualizar_estado(self):
        if len(self.jugadores.all()) == self.cantidad_jugadores:
            self.estado = EN_CURSO
            self.save()

    def __unicode__(self):
        return self.nombre

    """
    Crea una nueva ronda, estableciendo el jugador mano y pasandole los
    jugadores a la ronda.
    """
    def crear_ronda(self):
        ronda = Ronda(partida=self)
        ronda.mano_pos = self.mano_pos
        ronda.save()
        ronda.jugadores = self.jugadores.all()
        ronda.repartir()
        ronda.save()
        return ronda

    """
    Establece el jugador mano al jugador "de la derecha" del que es mano.
    """
    def actualizar_mano(self):
        self.mano_pos = (self.mano_pos + 1) % self.cantidad_jugadores
        self.save()

    """
    Actualiza el puntaje de cada jugador.
    Este metodo se llama cada vez que termina una ronda.
    """
    def actualizar_puntajes(self):
        ultima_ronda = list(self.ronda_set.all())[-1]
        puntos = ultima_ronda.calcular_puntos()
        self.puntos_e1 += puntos[0]
        self.puntos_e2 += puntos[1]
        self.save()


class Ronda(models.Model):
    partida = models.ForeignKey(Partida, verbose_name="partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo()
    mano_pos = models.IntegerField(max_length=1, default=0)
    termino = models.BooleanField(default=False)

    """
    Devuelve un mensaje con el ganador del envido y su puntaje,
    personalizado para jugador
    """
    def get_mensaje_ganador_envido(self,jugador):
        mensaje = ''
        try:
            canto = self.canto_set.get(tipo=ENVIDO)
        except:
            canto = None
        if canto and canto.estado == ACEPTADO:
            canto.envido.get_ganador()
            if canto.envido.equipo_ganador == jugador.equipo:
                mensaje = ('Ganamos el Envido con '
                            + str(canto.envido.maximo_puntaje)
                            + ' puntos.')
            else:
                mensaje = ('Ellos ganan el Envido con '
                            + str(canto.envido.maximo_puntaje)
                            + ' puntos.')
        return mensaje
    """
    Devuelve el ultimo canto de la ronda_set
    """
    def get_ultimo_canto(self):
        try:
            ultimo_canto = list(self.canto_set.all())[-1]
        except:
            ultimo_canto = None
        return ultimo_canto

    """
    Devuelve las opciones que tiene disponibles un jugador segun el estado de la ronda.
    """
    def get_opciones(self):
        canto = self.canto_set.filter(estado=NO_CONTESTADO)  # Hay un canto no contestado
        primer_enfrentamiento = list(self.enfrentamiento_set.all())[:1]
        if canto:
            # Si hay un canto que no fue contestado
            opciones = [QUIERO, NO_QUIERO]
        elif (primer_enfrentamiento and primer_enfrentamiento[0].get_termino()
                and all([int(mi_canto.tipo) != TRUCO for mi_canto in self.canto_set.all()])):
            # Termino el primer enfrentamiento y no se ha cantado truco aun
            opciones = [CANTAR_TRUCO]
        elif all([int(mi_canto.tipo) != ENVIDO for mi_canto in self.canto_set.all()]):
            # No se ha cantado envido aun y no se ha terminado el primer enfrentamiento
            opciones = [CANTAR_ENVIDO]
        else:
            # Ya se ha cantado envido y estamos en el primer enfrentamiento o
            # ya se canto el truco y se respondio
            opciones = None
        return opciones

    """
    Devuelve la cantidad de cartas que tiene el jugador adversario.
    """
    def cant_cartas_adversario(self, jugador):
        cant_cartas = [len(i.get_cartas_diponibles()) for i in self.jugadores.all() if i != jugador]
        return cant_cartas[0]

    """
    Devuelve una lista con las cartas que jugo el adversario.
    """
    def cartas_jugadas_adversario(self, jugador):
        cartas = [list(i.cartas_jugadas.all()) for i in self.jugadores.all() if i != jugador]
        return cartas[0]

    """
    Calcula de quien es el turno actual segun el estado de la ronda.
    """
    def get_turno(self):
        canto = self.canto_set.filter(estado=NO_CONTESTADO)
        enfrentamiento = list(self.enfrentamiento_set.all())[-1:]
        if canto:
            # Hay un canto que no se contesto aun, el turno es de quien debe responder
            turno_pos = (canto[0].pos_jugador_canto + 1) % len(self.jugadores.all())
        elif enfrentamiento and enfrentamiento[0].get_termino():
            # No hay un canto abierto, y el ultimo enfrentamiento termino
            turno_pos = enfrentamiento[0].get_ganador()  # El turno es del ganador
            if turno_pos == -1:
                # Si hubo un empate, el turno es del mano
                turno_pos = self.mano_pos
        elif enfrentamiento:
            # Hay un enfrentamiento sin terminar
            # El turno se calcula segun la cantidad de cartas del enfrentamiento
            jugador_que_empezo = enfrentamiento[0].jugador_empezo_pos
            cant_cartas_jugadas = len(enfrentamiento[0].cartas.all())
            turno_pos = (jugador_que_empezo + cant_cartas_jugadas) % len(self.jugadores.all())
        else:
            # No hay un canto abierto ni enfrentamientos existentes
            turno_pos = self.mano_pos
        turno_jugador = self.jugadores.all()[turno_pos]
        return turno_jugador

    """
    Reparte cartas a los jugadores.
    """
    def repartir(self):
        cartas_a_repartir = self.mazo.get_n_cartas(len(self.jugadores.all())*CARTAS_JUGADOR)
        desde = 0
        for jugador in self.jugadores.all():
            hasta = desde + 3
            jugador.asignar_cartas(cartas_a_repartir[desde:hasta])
            desde = desde + 3

    """
    Crea un enfrentamiento.
    """
    def crear_enfrentamiento(self, jugador):
        enfrentamiento = Enfrentamiento()
        enfrentamiento.ronda = self
        enfrentamiento.cantidad_jugadores = len(self.jugadores.all())
        enfrentamiento.jugador_empezo_pos = list(self.jugadores.all()).index(jugador)
        # Se necesita la posicion del jugador para saber de quien son las cartas
        enfrentamiento.save()
        return enfrentamiento


    """
    Crea un nuevo canto.
    """
    def crear_canto(self, tipo, jugador):
        if tipo == ENVIDO:
            canto = Envido(mano_pos=self.mano_pos)
        else:
            canto = Canto()
        canto.tipo = tipo
        canto.pts_en_juego = PTS_CANTO[tipo]
        canto.ronda = self
        canto.pos_jugador_canto = (list(self.jugadores.all())).index(jugador)
        # Se toma la posicion del jugador para el caso del empate del envido
        canto.mano_pos = self.mano_pos
        canto.save()
        canto.jugadores = self.jugadores.all()
        canto.save()

    """
    Devuelve el ultimo enfrentamiento de la ronda.
    Si no hay ninguno devuelve None.
    """
    def get_ultimo_enfrentamiento(self):
        try:
            ultimo_enfrentamiento = list(self.enfrentamiento_set.all())[-1]
        except:
            ultimo_enfrentamiento = None
        return ultimo_enfrentamiento

    """
    Se calculan los puntos.
    Este metodo se debe llamar cuando se termina la ronda.
    """
    def calcular_puntos(self):
        puntajes = [0, 0]
        enfrentamientos_ganados = [0, 0]
        # Verificamos si el truco estaba cantado
        canto = self.canto_set.filter(tipo=TRUCO)
        if canto and canto[0].estado == RECHAZADO:
            # Truco cantado y rechazado, por lo tanto ya hay un ganador
            puntajes[canto[0].equipo_ganador] += 1
        else:
            # Hay que calcular el ganador de los enfrentamientos
            ganador_enfrentamientos = self.get_ganador_enfrentamientos()
            puntajes[ganador_enfrentamientos] += 1
            if canto:
                # El Truco se canto y acepto, luego hay que definir el ganador
                canto[0].equipo_ganador = ganador_enfrentamientos
                canto[0].save()
        for canto in self.canto_set.all():
            # Asignamos los puntos correspondientes a los cantos
            equipo_ganador = canto.equipo_ganador
            puntajes[equipo_ganador] += canto.pts_en_juego
        return puntajes

    """
    Calcula que equipo gano mas enfrentamientos.
    Si hay un empate devuelve el equipo del mano.
    """
    def get_ganador_enfrentamientos(self):
        enfrentamientos_ganados = [0, 0]
        for enfrentamiento in self.enfrentamiento_set.all():
            ganador = enfrentamiento.get_ganador()
            if ganador >= 0:
                # No hubo un empate
                equipo_ganador = list(self.jugadores.all())[ganador].equipo
                enfrentamientos_ganados[equipo_ganador] += 1
        if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
            # Si se empataron los tres enfrentamientos
            ganador = self.jugadores.all()[self.mano_pos].equipo
        else:
            # Ganador es el equipo con mas enfrentamientos ganados
            ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
        return ganador

    """
    Si hay un ganador de la ronda devuelve true, si no, false.
    """
    def hay_ganador(self):
        # Devuelve verdadero si hay un ganador de la ronda
        result = False
        if len(self.enfrentamiento_set.all()) == 3:
            # Se jugaron los 3 enfrentamientos
            result = True
        elif len(self.enfrentamiento_set.all()) == 2:
            # Se jugaron 2 enfrentamientos
            enfrentamientos_ganados = [0, 0]
            for enfrentamiento in self.enfrentamiento_set.all():
                ganador = enfrentamiento.get_ganador()
                if ganador >= 0:
                    equipo_ganador = list(self.jugadores.all())[ganador].equipo
                    enfrentamientos_ganados[equipo_ganador] += 1
            if enfrentamientos_ganados[0] != enfrentamientos_ganados[1]:
                # Uno de los dos gano mas que el otro, luego gano la ronda
                result = True
        return result


class Canto(models.Model):
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    ronda = models.ForeignKey(Ronda, verbose_name="ronda")
    tipo = models.CharField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=1, default=1)
    equipo_ganador = models.IntegerField(max_length=1, default=-1)
    pos_jugador_canto = models.IntegerField(max_length=1)
    estado = models.IntegerField(max_length=1, default=NO_CONTESTADO)

    """
    Actualiza el estado del canto y los puntos en juego.
    """
    def aceptar(self):
        self.estado = ACEPTADO
        self.pts_en_juego += 1
        self.save()

    """
    Actualiza el estado del canto.
    """
    def rechazar(self):
        self.estado = RECHAZADO
        self.equipo_ganador = list(self.jugadores.all())[self.pos_jugador_canto].equipo
        self.save()


class Envido(Canto):
    mano_pos = models.IntegerField(max_length=1)
    maximo_puntaje = models.IntegerField(max_length=1,default=0)

    """
    Dada una posicion de un jugador, devuelve su distancia al jugador mano.
    """
    def dist_mano(self, pos_jugador):
        return (pos_jugador + 1) % (self.mano_pos + 1)

    """
    Calcula el ganador y los puntos del envido
    """
    def get_ganador(self):
        puntos_jugadores = []
        jugadores = self.jugadores.all()
        for jugador in jugadores:
            # Agrego a la lista los puntos de los jugadores
            puntos_jugadores.append(self.puntos_jugador(jugador))
        maximo_puntaje = max(puntos_jugadores)
        # Ganadores son aquellos que tienen el maximo_puntaje
        ganadores = [i for i, j in enumerate(puntos_jugadores) if j == maximo_puntaje]
        # Calculamos la distancia de un jugador al mano pues esto le da prioridad
        distanciasamano = map(self.dist_mano, ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        # El jugador ganador es el mano de los demas ganadores
        ganador_pos = ganadores[minposfrom]
        # El equipo ganador es el equipo del jugador ganador
        self.equipo_ganador = jugadores[ganador_pos].equipo
        self.maximo_puntaje = maximo_puntaje
        self.save()

    """
    Calcula los puntos de envido de un jugador.
    """
    def puntos_jugador(self, jugador):
        cartas = jugador.cartas.all()
        # Todas las combinaciones de sus cartas posibles
        comb = list(combinations(cartas, 2))
        # Maximo puntaje de una combinacion
        return max(map(self.puntos_2_cartas, comb))

    """
    Dada dos cartas devuelve el puntaje de envido que suman entre ellas.
    """
    def puntos_2_cartas(self, (carta1, carta2)):
        puntos = 0
        if carta1.palo == carta2.palo:
            puntos = 20 + carta1.valor_envido + carta2.valor_envido
        else:
            puntos = max(carta1.valor_envido, carta2.valor_envido)
        return puntos


class Enfrentamiento(models.Model):
    ronda = models.ForeignKey(Ronda, verbose_name="ronda")
    cartas = models.ManyToManyField(Carta, through='Tirada', verbose_name='cartas')
    jugador_empezo_pos = models.IntegerField(max_length=1)
    cantidad_jugadores = models.IntegerField(max_length=1, default=2)

    """
    Devuelve true si se termino un enfrentamiento.
    """
    def get_termino(self):
        return (len(self.cartas.all()) == self.cantidad_jugadores)

    """
    Esta funcion es invocada al finalizar un enfrentamiento
    y devuelve el ganador del mismo, o -1 en caso de empate.
    """
    def get_ganador(self):
        carta_puntaje_ganador = min(self.cartas.all(), key=lambda c: c.valor_jerarquico)
        maximo_puntaje = carta_puntaje_ganador.valor_jerarquico
        # Indices de las cartas del enfrentamiento que comparten el maximo_puntaje
        cartas_ganadoras = [i for i, j in enumerate(self.cartas.all()) if
                            j.valor_jerarquico == maximo_puntaje]
        if len(cartas_ganadoras) > 1:
            # Hay un empate, pues hay 2 cartas con el mismo valor jerarquico
            # En proximas iteraciones hay que diferenciar a que equipo pertenecen las cartas
            ganador_pos = -1
        else:
            # Ver documentacion: "Problema de orden en que se jugaron las cartas"
            # Orden en que fue jugada la carta ganadora. Ej: "la segunda carta"
            carta_ganadora_pos = list(self.cartas.order_by("tirada__orden")).index(carta_puntaje_ganador)
            # Calculamos a quien corresponde, segun quien empezo y la carta que gano
            ganador_pos = (self.jugador_empezo_pos + carta_ganadora_pos) % len(self.cartas.all())
        return ganador_pos

    """
    Agregamos una carta al enfrentamiento guardando el orden en que se tiro.
    """
    def agregar_carta(self, carta):
        tirada = Tirada.objects.create(carta=carta, enfrentamiento=self, orden=len(self.cartas.all()))
        tirada.save()


class Tirada(models.Model):
    carta = models.ForeignKey(Carta)
    enfrentamiento = models.ForeignKey(Enfrentamiento)
    orden = models.IntegerField(max_length=1, default=0)
