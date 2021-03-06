from django.db import models
from django.contrib.auth.models import User
from truco.constants import *
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from itertools import combinations
from operator import itemgetter, add
from django.db.models import Q


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
    posicion_mesa = models.IntegerField(max_length=1)

    """
    Asigna a cada jugador las cartas que se pasan como una lista de instancias de Carta.
    """
    def asignar_cartas(self, cartas):
        self.cartas = cartas
        self.cartas_disponibles = cartas
        self.save()

    """
    Devuelve las cartas de un jugador.
    """
    def get_cartas_disponibles(self):
        return list(self.cartas_disponibles.all())

    def __str__(self):
        return self.nombre


class Lobby:

    """
    Devuelve la lista de las partidas que estan en espera, es decir, no tiene
    todos los jugadores necesarios para empezar.
    """
    def get_lista_partidas(self):
        lista_partidas = Partida.objects.filter(estado=EN_ESPERA)
        return (lista_partidas)

    """
    Crea una nueva partida y une al usuario a la misma.
    """
    def crear_partida(self, user, nombre, puntos_objetivo, cantidad_jugadores):
        partida = Partida(nombre=nombre, puntos_objetivo=puntos_objetivo, cantidad_jugadores=cantidad_jugadores)
        partida.save()
        partida.agregar_jugador(user)
        return partida

    """
    Crea un jugador perteneciente a un usuario y lo pone en la partida.
    Devuelve 0 en caso de exito, -1 en caso contrario.
    """
    def unirse_partida(self, user, partida):
        result = 0
        if partida:
            for j in partida.jugadores.all():
                # Verifica que el usuario no este ya en la partida
                if j.user.id == user.id:
                    result = -1
            if result == 0:
                partida.agregar_jugador(user)
        else:
            result = -1
        return result


class Partida(models.Model):
    nombre = models.CharField(max_length=32)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntos_e1 = models.IntegerField(max_length=2, default=0)
    puntos_e2 = models.IntegerField(max_length=2, default=0)
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16, null=True)
    estado = models.IntegerField(default=EN_ESPERA)
    mano_pos = models.IntegerField(max_length=1, default=0)
    cantidad_jugadores = models.IntegerField(default=2)
    ronda_actual = models.ForeignKey('Ronda', null=True, related_name='ronda actual')

    """
    Obtiene una partida segun su id.
    Si no existe devuelve None.
    """
    @classmethod
    def get_partida(self, id_partida):
        try:
            partida = Partida.objects.get(pk=id_partida)
        except:
            partida = None
        return partida

    """
    Devuelve true si una partida esta lista para empezar una nueva ronda.
    Esto es, si no se llego a los puntos objetivo de la partida,los jugadores
    estan listos y no hay una ronda en curso.
    """
    def is_ready(self):
        ronda_terminada = True
        if self.ronda_actual:
            ronda_terminada = self.ronda_actual.hay_ganador()
        jugadores_listos = self.jugadores.count() == self.cantidad_jugadores
        ganador = self.get_ganador()  # Si ganador = -1 no hay ganador aun
        return ronda_terminada and jugadores_listos and ganador < 0

    """
    Devuelve la ronda actual si existe, None en caso contrario.
    """
    def get_ronda_actual(self):
        #Devuelve la ronda actual
        return self.ronda_actual

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
    Agrega jugadores a la partida, uno a cada equipo por orden de ingreso.
    """
    def agregar_jugador(self, user):
        jugador = Jugador(nombre=user.username, equipo=self.jugadores.count() % 2)
        jugador.user = user
        jugador.posicion_mesa = self.jugadores.count()
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
        if self.jugadores.count() == self.cantidad_jugadores:
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
        self.ronda_actual = ronda
        self.save()
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
        if self.ronda_actual:
            puntos = self.ronda_actual.calcular_puntos()
            self.puntos_e1 += puntos[0]
            self.puntos_e2 += puntos[1]
            self.save()

    """
    Devuelve la cantidad de puntos que vale el falta envido. Es decir, el minimo
    entre los puntos restantes para ganar la partida entre ambos equipos.
    """
    def get_min_pts_restantes(self):
        puntos_minimos = min(15 - self.puntos_e1 % 15, 15 - self.puntos_e2 % 15)
        return puntos_minimos


class Ronda(models.Model):
    partida = models.ForeignKey(Partida, verbose_name="partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo()
    mano_pos = models.IntegerField(max_length=1, default=0)
    primer_enfrentamiento = models.ForeignKey('Enfrentamiento', null=True, related_name='primer_enfrentamiento')
    segundo_enfrentamiento = models.ForeignKey('Enfrentamiento', null=True, related_name='segundo_enfrentamiento')
    tercer_enfrentamiento = models.ForeignKey('Enfrentamiento', null=True, related_name='tercer_enfrentamiento')
    equipo_mazo = models.IntegerField(max_length=1, default=-1) # Si un equipo se fue al mazo
    jugadores_listos = models.IntegerField(max_length=1, default=0)

    """
    Devuelve un mensaje con el ganador del envido y su puntaje,
    personalizado para jugador
    """
    def get_mensaje_ganador_envido(self, jugador):
        mensaje = ''
        if self.ultimo_envido() and self.ultimo_envido().todos_cantaron(self.jugadores.count() / 2):
            ganador, puntaje = self.ultimo_envido().get_supuesto_ganador()
            equipo_ganador = self.jugadores.get(posicion_mesa=ganador).equipo
            if equipo_ganador == jugador.equipo:
                mensaje = ('Ganamos el Envido con ' + str(puntaje) + ' puntos.')
            else:
                mensaje = ('Ellos ganan el Envido con ' + str(puntaje) + ' puntos.')
        return mensaje

    """
    Devuelve el mensaje que se mostrara de los cantos y las respuestas durante el juego
    """
    def get_mensaje_canto(self, jugador):
        mensaje = ''
        ultimo_canto = self.get_ultimo_canto()
        if ultimo_canto:
            jugador_canto = self.jugadores.get(posicion_mesa=ultimo_canto.pos_jugador_canto)
        if ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            mensaje = jugador_canto.nombre + " canto " + OPCIONES[int(ultimo_canto.tipo)]
        elif ultimo_canto and ultimo_canto.estado == ACEPTADO:
            if jugador.equipo == jugador_canto.equipo:
                mensaje = "Respondieron " + OPCIONES[int(QUIERO)]
            else:
                mensaje = "Respondimos " + OPCIONES[int(QUIERO)]
        elif ultimo_canto and ultimo_canto.estado == RECHAZADO:
            if jugador.equipo == jugador_canto.equipo:
                mensaje = "Respondieron " + OPCIONES[int(NO_QUIERO)]
            else:
                mensaje = "Respondimos " + OPCIONES[int(NO_QUIERO)]
        return mensaje

    """
    Devuelve el mensaje de los puntos cantados por los jugadores durante un envido.
    """
    def get_mensaje_puntos_cantados(self):
        mensaje = ''
        envido = self.ultimo_envido()
        puntos = -1
        if envido and envido.jugadores.count() > 0:
            jugador, puntos = envido.get_puntos_canto_ultimo_jugador()
            nombre_jugador = self.jugadores.get(posicion_mesa=jugador).nombre
        if puntos >= 0:
            # Si el jugador canto puntos
            mensaje += ("El jugador " + str(nombre_jugador) + " canto " + str(puntos) + " puntos" + "\n")
        elif puntos == -2:
            mensaje += "El jugador " + str(nombre_jugador) + " dijo: Son buenas\n"
        return mensaje

    """
    Devuelve las cartas que el jugador ya tiro en una ronda.
    """
    def get_cartas_jugadas(self, jugador):
        enfrentamientos = self.get_enfrentamientos()
        cant_jugadores = self.jugadores.count()
        cartas = []
        for i in range(cant_jugadores):
            cartas_jugador = []
            for enfrentamiento in enfrentamientos:
                cartas_jugador.append(enfrentamiento.carta_jugador((jugador.posicion_mesa + i) % cant_jugadores))
            cartas_jugador = [carta for carta in cartas_jugador if carta is not None]
            cartas.append(cartas_jugador)
        return cartas

    """
    Devuelve el ultimo canto de tipo envido o derivado cantado en la ronda.
    """
    def ultimo_envido(self):
        try:
            envido = self.envido_set.get(Q(estado=NO_CONTESTADO)|Q(estado=RECHAZADO))
        except:
            envido = None
        maximo = 0
        if not envido:
            for envido in self.envido_set.all():
                maximo = max(maximo, envido.pts_en_juego)
            try:
                envido = self.envido_set.get(pts_en_juego=maximo)
            except:
                envido = None
        return envido

    """
    Devuelve el ultimo canto de tipo truco o derivado cantado en la ronda.
    """
    def ultimo_truco(self):
        try:
            truco = self.truco_set.get(Q(estado=NO_CONTESTADO)|Q(estado=RECHAZADO))
        except:
            truco = None
        maximo = 0
        if not truco:
            for truco in self.truco_set.all():
                maximo = max(maximo,truco.pts_en_juego)
            try:
                truco = self.truco_set.get(pts_en_juego=maximo)
            except:
                truco = None
        return truco

    """
    Devuelve el ultimo canto realizado en la ronda.
    """
    def get_ultimo_canto(self):
        result = None
        if self.ultimo_truco():
            result = self.ultimo_truco()
        elif self.ultimo_envido():
            result = self.ultimo_envido()
        return result

    """
    Devuelve true si el jugador en turno tiene la posibilidad de tirar una carta. Esto
    sucede cuando no hay un canto sin contestar.
    """
    def se_puede_tirar(self):
        result = True
        ultimo_canto = self.get_ultimo_canto()
        if ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            result = False
        elif self.se_debe_cantar_puntos():
            result = False
        return result

    """
    Devuelve true si hay un envido aceptado y los jugadores deben cantar sus puntos.
    """
    def se_debe_cantar_puntos(self):
        envido = self.ultimo_envido()
        return (envido and envido.estado == ACEPTADO
                and not envido.todos_cantaron((self.jugadores.count() / 2)))
                # Ya nadie mas tiene que cantar

    """
    Devuelve la posicion del jugador que debe cantar puntos
    """
    def jugador_tiene_que_cantar_puntos(self):
        turno = self.mano_pos
        envido = self.ultimo_envido()
        if envido.jugadores.count() > 0:
            # Si el mano ya canto sus puntos
            ultimo_canto_perdiendo = envido.ultimo_que_canto_equipo_perdiendo()
            if ultimo_canto_perdiendo >= 0:
                # Alguno de los que va perdiendo cantos
                turno = (envido.ultimo_que_canto_equipo_perdiendo() + 2) % self.jugadores.count()
            else:
                turno = (self.mano_pos + 1) % self.jugadores.count()
        return turno

    """
    Devuelve la posicion del jugador pie del equipo que se pasa como parametro
    """
    def get_pie(self, equipo):
        equipo_mano = self.jugadores.get(posicion_mesa=self.mano_pos).equipo
        if equipo == equipo_mano:
            turno = (self.mano_pos + self.jugadores.count() - 2) % self.jugadores.count()
        else:
            turno = (self.mano_pos + self.jugadores.count() - 1) % self.jugadores.count()
        return turno

    """
    Devuelve las opciones que tiene disponibles un jugador segun el estado de la ronda.
    """
    def get_opciones(self):
        ultimo_canto = self.get_ultimo_canto()
        opciones = []
        if ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            # Si hay un canto que no fue contestado
            opciones = [QUIERO, NO_QUIERO]
            opciones.extend(ultimo_canto.get_respuestas())
        elif (self.primer_enfrentamiento and self.primer_enfrentamiento.get_termino()
                and not self.ultimo_truco()):
            # Termino el primer enfrentamiento y no se ha cantado truco aun
            opciones = [TRUCO, IRSE_AL_MAZO]
        elif (not self.ultimo_envido()
              and not (self.primer_enfrentamiento and self.primer_enfrentamiento.get_termino())):
                # No se puede cantar envido si termina el primer enfrentamiento
                opciones = [ENVIDO, REAL_ENVIDO, FALTA_ENVIDO, IRSE_AL_MAZO]
        else:
            # Ya se ha cantado envido y estamos en el primer enfrentamiento o
            # ya se canto el truco y se respondio
            if self.se_debe_cantar_puntos() and self.ultimo_envido().jugadores.count() > 0:
                opciones.extend([SON_BUENAS])
            elif self.se_debe_cantar_puntos():
                opciones = []
            elif self.ultimo_truco():
                jugador_canto = self.jugadores.get(posicion_mesa=self.ultimo_truco().pos_jugador_canto)
                if not self.get_turno().equipo == jugador_canto.equipo:
                    opciones = self.ultimo_truco().get_respuestas()
                opciones.append(IRSE_AL_MAZO)
            else:
                opciones = [IRSE_AL_MAZO]
        return opciones

    """
    Devuelve un arreglo con la cantidad de cartas de todos los jugadores, a excepcion
    del jugador que se pasa como parametro.
    """
    def cant_cartas_adversario(self, jugador): #___Cambiar le nombre por adversarios
        cantidad_jugadores = self.jugadores.count()
        cant_cartas = []
        for i in range(cantidad_jugadores - 1):
            # Para todos los demas jugadores
            posicion = (jugador.posicion_mesa + 1 + i) % cantidad_jugadores
            # jugador_observado: es el jugador del cual se estan calculando las cartas que posee
            jugador_observado = self.jugadores.get(posicion_mesa=posicion)
            cant_cartas.append(len(jugador_observado.get_cartas_disponibles()))
        return cant_cartas

    """
    Devuelve una lista con todos los jugadores, comenzando con el nombre del jugador que se pasa como
    parametro y continuando hacia los jugadores a la derecha
    """
    def nombres_jugadores(self, jugador):
        cantidad_jugadores = self.jugadores.count()
        nombres = []
        for i in range(cantidad_jugadores):
            posicion = (jugador.posicion_mesa + i) % cantidad_jugadores
            jugador_observado = self.jugadores.get(posicion_mesa=posicion)
            nombres.append(jugador_observado.nombre)
        return nombres

    """
    Calcula de quien es el turno actual segun el estado de la ronda y devuelve al jugador en turno
    """
    def get_turno(self):
        ultimo_canto = self.get_ultimo_canto()
        ultimo_enfrentamiento = self.get_ultimo_enfrentamiento()
        if self.hay_ganador() and not self.todos_jugadores_listos():
            turno_pos = self.turno_fin_ronda()
        elif ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            # Hay un canto que no se contesto aun, el turno es de quien debe responder
            equipo_canto = self.jugadores.get(posicion_mesa = ultimo_canto.pos_jugador_canto).equipo
            turno_pos = self.get_pie((equipo_canto + 1) % 2)
        elif self.se_debe_cantar_puntos():
            turno_pos = self.jugador_tiene_que_cantar_puntos()
        elif ultimo_enfrentamiento and ultimo_enfrentamiento.get_termino():
            # No hay un canto abierto, y el ultimo enfrentamiento termino
            turno_pos = ultimo_enfrentamiento.get_ganador()  # El turno es del ganador
            if turno_pos == -1:
                # Si hubo un empate, el turno es del mano
                turno_pos = self.mano_pos
        elif ultimo_enfrentamiento:
            # Hay un enfrentamiento sin terminar
            # El turno se calcula segun la cantidad de cartas del enfrentamiento
            jugador_que_empezo = ultimo_enfrentamiento.jugador_empezo_pos
            cant_cartas_jugadas = ultimo_enfrentamiento.cartas.count()
            turno_pos = (jugador_que_empezo + cant_cartas_jugadas) % self.jugadores.count()
        else:
            # No hay un canto abierto ni enfrentamientos existentes
            turno_pos = self.mano_pos
        jugador_en_turno = self.jugadores.get(posicion_mesa=turno_pos)
        return jugador_en_turno

    """
    Reparte cartas a los jugadores.
    """
    def repartir(self):
        cartas_a_repartir = self.mazo.get_n_cartas(self.jugadores.count() * CARTAS_JUGADOR)
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
        enfrentamiento.cantidad_jugadores = self.jugadores.count()
        # Se necesita la posicion del jugador para saber de quien son las cartas
        enfrentamiento.jugador_empezo_pos = jugador.posicion_mesa
        enfrentamiento.save()
        if not self.primer_enfrentamiento:
            self.primer_enfrentamiento = enfrentamiento
        elif not self.segundo_enfrentamiento:
            self.segundo_enfrentamiento = enfrentamiento
        else:
            self.tercer_enfrentamiento = enfrentamiento
        self.save()
        return enfrentamiento

    """
    Crea un nuevo canto.
    """
    def crear_canto(self, tipo, jugador, puntos):
        if tipo in [ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]:
            canto = Envido(mano_pos=self.mano_pos, puntos_falta=puntos, ronda=self, tipo=tipo)
            canto.pos_jugador_canto = jugador.posicion_mesa
            canto.mano_pos = self.mano_pos
            canto.save()
        else:
            canto = Truco()
            canto.tipo = tipo
            canto.ronda = self
            canto.pos_jugador_canto = jugador.posicion_mesa
            # Se toma la posicion del jugador para el caso del empate del envido
            canto.mano_pos = self.mano_pos
            canto.save()

    """
    Devuelve el ultimo enfrentamiento de la ronda.
    Si no hay ninguno devuelve None.
    """
    def get_ultimo_enfrentamiento(self):
        result = None
        if self.tercer_enfrentamiento:
            result = self.tercer_enfrentamiento
        elif self.segundo_enfrentamiento:
            result = self.segundo_enfrentamiento
        else:
            result = self.primer_enfrentamiento
        return result

    """
    Se calculan los puntos.
    Este metodo se debe llamar cuando se termina la ronda.
    """
    def calcular_puntos(self):
        enfrentamientos_ganados = [0, 0]
        puntajes = self.calcular_puntos_envido()
        if self.ultimo_truco() and self.ultimo_truco().estado == RECHAZADO:
            # Truco cantado y rechazado, por lo tanto ya hay un ganador
            equipo_ganador = self.jugadores.get(
                posicion_mesa=self.ultimo_truco().pos_jugador_canto
                ).equipo
            puntajes[equipo_ganador] += self.ultimo_truco().pts_en_juego
        else:
            # Hay que calcular el ganador de los enfrentamientos
            ganador_enfrentamientos = self.get_ganador_enfrentamientos()
            if self.ultimo_truco():
                # El Truco se canto y acepto, luego hay que definir el ganador
                puntajes[ganador_enfrentamientos] += self.ultimo_truco().pts_en_juego
            else:
                if not self.primer_enfrentamiento and not self.ultimo_envido():
                    # Si el mano no canto envido y se fue en la primer mano
                    puntajes[ganador_enfrentamientos] += 2
                else:
                    puntajes[ganador_enfrentamientos] += 1
        return puntajes

    """
    Calcula los puntos que le corresponden a los jugadores despues de haber aceptado
    o rechazado un envido.
    """
    def calcular_puntos_envido(self):
        puntajes = [0, 0]
        envido = self.ultimo_envido()
        if envido and envido.estado == RECHAZADO:
            equipo_ganador = self.jugadores.get(posicion_mesa=envido.pos_jugador_canto).equipo
            puntajes[equipo_ganador] += envido.pts_en_juego
        elif envido:
            equipo_ganador = envido.get_equipo_ganador()
            puntajes[equipo_ganador] += envido.pts_en_juego
        return puntajes

    """
    Devuelve los enfrentamientos de la ronda.
    """
    def get_enfrentamientos(self):
        enfrentamientos = [self.primer_enfrentamiento, self.segundo_enfrentamiento, self.tercer_enfrentamiento]
        enfrentamientos = [enf for enf in enfrentamientos if enf is not None]
        return enfrentamientos

    """
    Calcula que equipo gano mas enfrentamientos.
    Si hay un empate devuelve el equipo del mano.
    """
    def get_ganador_enfrentamientos(self):
        if self.equipo_mazo >= 0:
            ganador = (self.equipo_mazo + 1) % 2
        else:
            enfrentamientos_ganados = [0, 0]
            enfrentamientos = self.get_enfrentamientos()
            for enfrentamiento in enfrentamientos:
                ganador = enfrentamiento.get_ganador()
                if ganador >= 0:
                    # No hubo un empate
                    equipo_ganador = self.jugadores.get(posicion_mesa=ganador).equipo
                    enfrentamientos_ganados[equipo_ganador] += 1
                else:
                    if enfrentamiento == self.tercer_enfrentamiento and self.primer_enfrentamiento.get_ganador() > 0:
                        equipo_ganador = self.primer_enfrentamiento.get_ganador()
                        enfrentamientos_ganados[equipo_ganador] += 1
            if enfrentamientos_ganados[0] == enfrentamientos_ganados[1]:
                # Si se empataron los tres enfrentamientos
                ganador = self.jugadores.all()[self.mano_pos].equipo
            else:
                # Ganador es el equipo con mas enfrentamientos ganados
                ganador = enfrentamientos_ganados.index(max(enfrentamientos_ganados))
        return ganador

    """
    Este metodo se debe llamar cuando algun jugador se va al mazo
    """
    def irse_al_mazo(self, jugador):
        #seteo el equipo que se fue al mazo
        self.equipo_mazo = jugador.equipo
        self.save()

    """
    Si hay un ganador de la ronda devuelve true, si no, false.
    """
    def hay_ganador(self):
        # Devuelve verdadero si hay un ganador de la ronda
        result = False
        if self.equipo_mazo >= 0:
            # Si un jugador se fue al mazo hay un ganador
            result = True
        elif self.ultimo_truco() and self.ultimo_truco().estado == RECHAZADO:
            # Si no se quizo el truco
            result = True
        elif self.tercer_enfrentamiento and self.tercer_enfrentamiento.get_termino():
            # Se jugaron los 3 enfrentamientos
            result = True
        elif (self.segundo_enfrentamiento and not self.tercer_enfrentamiento
                and self.segundo_enfrentamiento.get_termino()):
            # Se jugaron 2 enfrentamientos
            enfrentamientos_ganados = [0, 0]
            enfrentamientos = self.get_enfrentamientos()
            for enfrentamiento in enfrentamientos:
                ganador = enfrentamiento.get_ganador()
                if ganador >= 0:
                    equipo_ganador = self.jugadores.get(posicion_mesa=ganador).equipo
                    enfrentamientos_ganados[equipo_ganador] += 1
            if enfrentamientos_ganados[0] != enfrentamientos_ganados[1]:
                # Uno de los dos gano mas que el otro, luego gano la ronda
                result = True
        return result

    """
    Devuelve true cuando ambos jugadores pie eligieron ir a
    la siguiente ronda.
    """
    def todos_jugadores_listos(self):
        return(self.jugadores_listos == 2)

    """
    Suma un jugador listo al conteo de jugadores listos de la ronda.
    """
    def jugador_listo(self):
        self.jugadores_listos += 1
        self.save()

    """
    Devuelve las opciones al finalizar la ronda. Si se jugo un envido se muestra
    pedir los puntos y siguiente ronda, si no, solo siguiente ronda.
    Si se piden mostrar los puntos, devolvera la opcion de mostrar los puntos.
    """
    def get_opciones_fin_ronda(self):
        opciones = [SIGUIENTE_RONDA]
        envido = self.ultimo_envido()
        if (envido and envido.puntos_pedidos and not envido.puntos_mostrados):
                supuesto_ganador = self.jugadores.get(posicion_mesa=envido.get_supuesto_ganador()[0])
                posicion_pie = self.get_pie(supuesto_ganador.equipo)
                if self.get_turno().posicion_mesa == posicion_pie:
                    opciones.append(MOSTRAR_PUNTOS)
        elif (envido and self.jugadores_listos == 0 and not envido.puntos_pedidos
                and envido.estado == ACEPTADO):
            opciones.append(PEDIR_PUNTOS)
        return opciones

    """
    Devuelve la posicion en la mesa del jugador que esta en turno al finalizar la ronda
    """
    def turno_fin_ronda(self):
        # Partimos de la cantidad de jugadores que hicieron click en siguiente ronda.
        cant_acciones = self.jugadores_listos
        envido = self.ultimo_envido()
        if envido and envido.estado == ACEPTADO:
            # Hay un envido aceptado
            if envido.puntos_pedidos:
                cant_acciones += 1
            if envido.puntos_mostrados:
                cant_acciones += 1
            pos_supuesto_ganador = envido.get_supuesto_ganador()[0]
            equipo_ganador = self.jugadores.get(posicion_mesa=pos_supuesto_ganador).equipo
            if cant_acciones % 2 == 0:
                equipo_perdedor = (equipo_ganador + 1) % 2
                turno_pos = self.get_pie(equipo_perdedor)
            else:
                turno_pos = self.get_pie(equipo_ganador)
        else:
            equipo_mano = self.jugadores.get(posicion_mesa=self.mano_pos).equipo
            # Si el pie del mano hizo click en siguiente ronda, se le da el turno al otro pie.
            # Sino al pie del mano.
            turno_pos = (self.get_pie(equipo_mano) + cant_acciones) % self.jugadores.count()
        return turno_pos

    """
    Devuelve true si el equipo que perdio el envido pidio ver los puntos.
    """
    def hay_que_mostrar_los_puntos(self):
        envido = self.ultimo_envido()
        return(envido and envido.puntos_mostrados and self.jugadores_listos == 0)


class Canto(models.Model):
    ronda = models.ForeignKey(Ronda, verbose_name="ronda")
    tipo = models.IntegerField(max_length=1)
    pts_en_juego = models.IntegerField(max_length=2, default=1)
    pos_jugador_canto = models.IntegerField(max_length=1)
    estado = models.IntegerField(max_length=1, default=NO_CONTESTADO)

    class Meta:
        abstract = True

    """
    Actualiza el estado del canto y los puntos en juego.
    """
    def aceptar(self):
        pass

    """
    Actualiza el estado del canto.
    """
    def rechazar(self):
        self.estado = RECHAZADO
        self.save()


class Truco(Canto):

    """
    Actualiza el estado del canto y los puntos en juego.
    """
    def aceptar(self):
        self.estado = ACEPTADO
        self.pts_en_juego += 1
        self.save()

    """
    Devuelve las opciones posibles para recantar el truco
    """
    def get_respuestas(self):
        result = []
        nombre_canto = self.tipo
        # Aumenta la apuesta al siguiente canto
        if nombre_canto < VALE_CUATRO:
            nombre_canto += 1
            result.append(nombre_canto)
        return result

    """
    Aumentar crea un nuevo canto de mayor valor, con
    los puntos que ya estan en juego. Es decir los que le corresponden
    a un jugador si el otro no quiere lo que se canto.
    """
    def aumentar(self, nombre_canto, pos_jugador_canto):
        if self.estado == NO_CONTESTADO:
            self.aceptar()
        # Se crea una nueva instancia para el canto de mayor valor
        result = Truco(
            ronda=self.ronda,
            tipo=nombre_canto,
            pts_en_juego=self.pts_en_juego,
            pos_jugador_canto=pos_jugador_canto,
            )
        result.save()
        return result


class Envido(Canto):
    jugadores = models.ManyToManyField(Jugador, through='JugadorEnEnvido', verbose_name='jugadores')
    mano_pos = models.IntegerField(max_length=1)
    puntos_pedidos = models.BooleanField(default=False)
    puntos_mostrados = models.BooleanField(default=False)
    puntos_falta = models.IntegerField(max_length=2, default=0)  # Puntos en caso que se gane la falta envido

    """
    Cambia el estado de un envido a aceptado y establece los puntos en juego segun
    lo que se canto.
    """
    def aceptar(self):
        self.estado = ACEPTADO
        if self.tipo == FALTA_ENVIDO:
            self.pts_en_juego = self.puntos_falta
        elif self.tipo == ENVIDO:
            self.pts_en_juego += 1
        elif self.tipo == DOBLE_ENVIDO:
            self.pts_en_juego += 2
        else:
            if self.pts_en_juego > 1:
                # Si se canta real envido con otro canto antes
                self.pts_en_juego += 3
            else:
                self.pts_en_juego += 2
        self.save()

    """
    Devuelve un nuevo canto creado con los puntos en juego del canto anterior aceptado.
    El estado del canto anterior se convierte en aceptado.
    """
    def aumentar(self, tipo, pos_jugador_canto):
        self.aceptar()
        canto = Envido(puntos_falta=self.puntos_falta, ronda=self.ronda,
                       pos_jugador_canto=pos_jugador_canto,
                       pts_en_juego=self.pts_en_juego,
                       tipo=tipo, mano_pos=self.mano_pos)
        canto.save()
        return canto

    """
    Respuestas que tiene un jugador para contestar un envido o derivado
    """
    def get_respuestas(self):
        if self.tipo == ENVIDO:
            opciones = [DOBLE_ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]
        elif self.tipo == DOBLE_ENVIDO:
            opciones = [REAL_ENVIDO, FALTA_ENVIDO]
        elif self.tipo == REAL_ENVIDO:
            opciones = [FALTA_ENVIDO]
        else:
            # Si es falta envido
            opciones = []
        return opciones

    """
    Dada una posicion de un jugador, devuelve su distancia al jugador mano.
    """
    def dist_mano(self, pos_jugador):
        cantidad_jugadores = self.jugadores.count()
        if pos_jugador >= self.mano_pos:
            distancia = pos_jugador - self.mano_pos
        else:
            distancia = cantidad_jugadores - self.mano_pos + pos_jugador
        return distancia

    """
    Calcula los puntos de envido de un jugador. Devuelve una tupla con los puntos y las cartas que los conforman.
    """
    def puntos_jugador(self, jugador):
        cartas = jugador.cartas.all()
        # Todas las combinaciones de sus cartas posibles
        comb = list(combinations(cartas, 2))
        # Maximo puntaje de una combinacion
        puntajes_cartas = map(self.puntos_2_cartas, comb)
        maximo_puntaje = max(puntajes_cartas, key=itemgetter(0))
        return maximo_puntaje

    """
    Dada dos cartas devuelve una lista con el puntaje de envido que suman entre ellas y las cartas que lo conforman.
    """
    def puntos_2_cartas(self, (carta1, carta2)):
        if carta1.palo == carta2.palo:
            puntos = 20 + carta1.valor_envido + carta2.valor_envido
            result = (puntos, [carta1, carta2])
        else:
            puntos = max(carta1.valor_envido, carta2.valor_envido)
            if puntos == carta1.valor_envido:
                result = (puntos, [carta1])
            else:
                result = (puntos, [carta2])
        return result

    """
    Esta funcion devuelve una lista de tuplas donde cada tupla esta compuesta
    por la posicion en mesa de jugador y los puntos que canto.
    """
    def get_puntos_jugadores(self):
        puntos_jugadores = []
        for jugador in self.jugadores.all():
            # Agrego a la lista los puntos de los jugadores
            jugador_EnEnvido = jugador.jugadorenenvido_set.get(envido=self)
            puntos_jugadores.append((jugador.posicion_mesa, jugador_EnEnvido.puntos_canto))
        return puntos_jugadores

    def get_puntos_canto_ultimo_jugador(self):
        jugadores = self.jugadores.all()
        maximo_orden = max([jugador.jugadorenenvido_set.get(envido=self).orden for jugador in jugadores])
        jugador = JugadorEnEnvido.objects.get(envido=self,orden=maximo_orden).jugador
        puntos = JugadorEnEnvido.objects.get(envido=self,orden=maximo_orden).puntos_canto
        posicion = jugador.posicion_mesa
        # jugador = self.jugadores.get(jugadorenenvido__orden = maximo_orden)
        # posicion = jugador.posicion_mesa
        # puntos = jugador.jugadorenenvido_set.get(envido=self).puntos_canto
        return (posicion, puntos)

    """
    Esta funcion calcula la posicion en la mesa del jugador ganador y el puntaje
    maximo del mismo segun los puntos cantados, no necesariamente los que conforman
    las cartas de cada jugador.
    """
    def get_supuesto_ganador(self):
        puntos_jugadores = self.get_puntos_jugadores()
        maximo_puntaje = max(puntos_jugadores, key=itemgetter(1))[1]
        # Ganadores son aquellos que tienen el maximo_puntaje
        ganadores = [i for i, j in puntos_jugadores if j == maximo_puntaje]
        # Calculamos la distancia de un jugador al mano pues esto le da prioridad
        distanciasamano = map(self.dist_mano, ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        # El jugador ganador es el mano de los demas ganadores
        ganador_pos = ganadores[minposfrom]
        # El equipo ganador es el equipo del jugador ganador
        maximo_puntaje = maximo_puntaje
        return(ganador_pos, maximo_puntaje)

    """
    Devuelve el numero del equipo ganador.
    """
    def get_equipo_ganador(self):
        supuesto_ganador = self.get_supuesto_ganador()
        jugador_supuesto_ganador = self.jugadores.get(posicion_mesa=supuesto_ganador[0])
        supuestos_puntos_supuesto_ganador = supuesto_ganador[1]
        equipo_supuesto_ganador = jugador_supuesto_ganador.equipo
        equipo_supuesto_perdedor = (equipo_supuesto_ganador + 1) % 2
        if not self.puntos_pedidos:
            # Se pidieron ver los puntos en el final de la ronda
            ganador = equipo_supuesto_ganador
        elif not self.puntos_mostrados:
            # Si se pidieron y no se mostraron, se pasan los puntos del envido al otro equipo
            ganador = equipo_supuesto_perdedor
        else:
            # Se piden ver los puntos y se muestran
            puntos_supuesto_ganador = self.puntos_jugador(jugador_supuesto_ganador)[0]
            if puntos_supuesto_ganador == supuestos_puntos_supuesto_ganador:
                # Si no mintio, conserva sus puntos
                ganador = equipo_supuesto_ganador
            else:
                # Si mintio, los puntos son del otro
                ganador = equipo_supuesto_perdedor
        return ganador

    """
    Guarda los puntos cantados por los jugadores durante un envido aceptado.
    """
    def cantar_puntos(self, jugador, puntos):
        jugadorEnEnvido = JugadorEnEnvido(jugador=jugador,
                                          envido=self,
                                          puntos_canto=puntos,
                                          orden=self.jugadores.count())
        jugadorEnEnvido.save()

    """
    Devuelve true si todos los jugadores de la mesa cantaron sus puntos.
    """
    def todos_cantaron(self, cant_jug_en_equipo):
        result = False
        if self.jugadores.count() > 0:
            supuesto_ganador = self.get_supuesto_ganador()[0]
            equipo_perdiendo = (self.jugadores.get(posicion_mesa=supuesto_ganador).equipo + 1) % 2
            result = (self.jugadores.filter(equipo=equipo_perdiendo).count() == cant_jug_en_equipo)
        return result
    
    """
    Guarda en la base de datos que el equipo perdedor del envido pidio ver los puntos.
    """
    def pedir_puntos(self):
        self.puntos_pedidos = True
        self.save()

    """
    Guarda en la base de datos que el equipo ganador del envido eligio mostrar los puntos.
    """
    def mostrar_puntos(self):
        self.puntos_mostrados = True
        self.save()

    """
    Devuelve las cartas del jugador que gano el envido. Si el jugador mintio,
    se muestran todas las cartas de ese jugador. Si no, se muestran solo las que
    conforman el envido.
    """
    def get_puntos_a_mostrar(self):
        pos_supuesto_ganador, supuestos_puntos_supuesto_ganador = self.get_supuesto_ganador()
        jugador_supuesto_ganador = self.jugadores.get(posicion_mesa=pos_supuesto_ganador)
        puntos_reales, cartas_de_puntos = self.puntos_jugador(jugador_supuesto_ganador)
        if puntos_reales == supuestos_puntos_supuesto_ganador:
            # Si el oponente canto bien, se muestran las cartas que componen el envido
            cartas = cartas_de_puntos
        else:
            # Si el jugador mintio
            cartas = list(jugador_supuesto_ganador.cartas.all())
        return cartas

    """
    Devuelve la posicion en mesa del ultimo jugador que canto y pertenece al equipo que
    parcialmente va perdiendo el envido(mientras se cantan los puntos), o -1 si ninguno
    de ellos canto aun.
    """
    def ultimo_que_canto_equipo_perdiendo(self):
        # Ya canto puntos algun jugador
        ganador_parcial_pos = self.get_supuesto_ganador()[0]
        equipo_perdiendo = (self.jugadores.get(posicion_mesa=ganador_parcial_pos).equipo + 1) % 2
        # Jugadores que ya cantaron del equipo que va perdiendo.
        jug_equipo_perdiendo_que_ya_cantaron = self.jugadores.filter(equipo=equipo_perdiendo)
        ultimo_en_cantar = -1 # Este valor indica que ninguno del equipo que esta perdiendo canto aun.
        if jug_equipo_perdiendo_que_ya_cantaron:
            # Algun jugador del equipo que esta perdiendo ya canto
            # Sus posiciones en la mesa
            posiciones_en_mesa = [jugador.posicion_mesa for jugador in jug_equipo_perdiendo_que_ya_cantaron]
            # Sus distancias al jugador mano
            distancias_a_mano = map(self.dist_mano, posiciones_en_mesa)
            # Indice en lista posiciones_en_mesa de la posicion mas lejana al mano
            jugador_mas_lejos_index = distancias_a_mano.index(max(distancias_a_mano))
            # Posicion en mesa del jugador que ya canto, pertenece al equipo que va perdiendo
            # y esta mas alejado del mano
            ultimo_en_cantar = posiciones_en_mesa[jugador_mas_lejos_index]
            # Debe cantar el siguiente del mismo equipo
        return ultimo_en_cantar


class JugadorEnEnvido(models.Model):
    jugador = models.ForeignKey(Jugador, verbose_name='jugador')
    envido = models.ForeignKey(Envido, verbose_name='envido')
    puntos_canto = models.IntegerField(max_length=2, null=True)
    orden = models.IntegerField(max_length=1, default=0)


class Enfrentamiento(models.Model):
    cartas = models.ManyToManyField(Carta, through='Tirada', verbose_name='cartas')
    jugador_empezo_pos = models.IntegerField(max_length=1)
    cantidad_jugadores = models.IntegerField(max_length=1, default=2)

    """
    Devuelve true si se termino un enfrentamiento.
    """
    def get_termino(self):
        return self.cartas.count() == self.cantidad_jugadores

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
            # Orden en que fue jugada la carta ganadora. Ej: "la segunda carta"
            carta_ganadora_pos = carta_puntaje_ganador.tirada_set.get(enfrentamiento=self).orden
            # Calculamos a quien corresponde, segun quien empezo y la carta que gano
            ganador_pos = (self.jugador_empezo_pos + carta_ganadora_pos) % self.cartas.count()
        return ganador_pos

    """
    Agregamos una carta al enfrentamiento guardando el orden en que se tiro.
    """
    def agregar_carta(self, carta):
        tirada = Tirada.objects.create(carta=carta, enfrentamiento=self, orden=self.cartas.count())
        tirada.save()

    """
    Dada la posicion de un jugador devuelve su carta en el enfrentamiento,
    si el jugador no posee carta en el enfrentamiento devuelve None
    """
    def carta_jugador(self, jugador_pos):
        # Calculamos la posicion de la carta en el enfrentamiento
        if jugador_pos >= self.jugador_empezo_pos:
            pos_carta = jugador_pos - self.jugador_empezo_pos
        else:
            pos_carta = self.cantidad_jugadores - self.jugador_empezo_pos + jugador_pos
        try:
            carta = self.cartas.get(tirada__orden=pos_carta)
        except:
            carta = None
        return carta


class Tirada(models.Model):
    carta = models.ForeignKey(Carta)
    enfrentamiento = models.ForeignKey(Enfrentamiento)
    orden = models.IntegerField(max_length=1, default=0)
