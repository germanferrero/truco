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
    def get_cartas_diponibles(self):
        return list(self.cartas_disponibles.all())


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
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=EN_ESPERA)
    mano_pos = models.IntegerField(max_length=1, default=0)
    cantidad_jugadores = models.IntegerField(default=2)
    ronda_actual = models.ForeignKey('Ronda',null=True, related_name='ronda actual')
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
        #Devuelve la ronda acutal
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


    def get_min_pts_restantes(self):
        puntos_minimos = min(15 - self.puntos_e1 % 15, 15 - self.puntos_e2 % 15)
        return puntos_minimos


class Ronda(models.Model):
    partida = models.ForeignKey(Partida, verbose_name="partida")
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    mazo = Mazo()
    mano_pos = models.IntegerField(max_length=1, default=0)
    ultimo_envido = models.ForeignKey('Envido',null=True,related_name='ultimo envido')
    ultimo_truco = models.ForeignKey('Truco',null=True,related_name='ultimo truco')
    primer_enfrentamiento = models.ForeignKey('Enfrentamiento',null=True,related_name='primer_enfrentamiento')
    segundo_enfrentamiento = models.ForeignKey('Enfrentamiento',null=True,related_name='segundo_enfrentamiento')
    tercer_enfrentamiento = models.ForeignKey('Enfrentamiento',null=True,related_name='tercer_enfrentamiento')
    equipo_mazo = models.IntegerField(max_length=1, default=-1)
    jugadores_listos = models.IntegerField(max_length=1, default=0)

    """
    Devuelve un mensaje con el ganador del envido y su puntaje,
    personalizado para jugador
    """
    def get_mensaje_ganador_envido(self,jugador):
        mensaje = ''
        if self.ultimo_envido and self.ultimo_envido.todos_cantaron():
            ganador,puntaje = self.ultimo_envido.get_supuesto_ganador()
            equipo_ganador = self.jugadores.get(posicion_mesa=ganador).equipo
            if equipo_ganador == jugador.equipo:
                mensaje = ('Ganamos el Envido con '
                            + str(puntaje)
                            + ' puntos.')
            else:
                mensaje = ('Ellos ganan el Envido con '
                            + str(puntaje)
                            + ' puntos.')
        return mensaje
    """
    Devuelve el mensaje con de juego, cantos y respuestas
    """
    def get_mensaje_canto(self, jugador):
        mensaje = ''
        if self.get_turno() == jugador:
            ultimo_canto = self.get_ultimo_canto()
            if ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
                mensaje = OPCIONES[int(ultimo_canto.tipo)]
            elif ultimo_canto and ultimo_canto.estado == ACEPTADO:
                mensaje = OPCIONES[int(QUIERO)]
                if int(ultimo_canto.tipo) in [ENVIDO, DOBLE_ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]:
                    # Si es un canto de tipo envido y fue aceptado
                    puntos_oponente = ultimo_canto.get_puntos_cantados_oponente()
                    if puntos_oponente >= 0:
                        # Si otro ya canto los puntos
                        mensaje += (".\n El oponente canto: " + str(puntos_oponente))
                    elif puntos_oponente == -2:
                        mensaje += ".\n El oponente dijo: Son buenas"
            elif ultimo_canto and ultimo_canto.estado == RECHAZADO:
                mensaje = OPCIONES[int(NO_QUIERO)]
        return mensaje

    """
    Devuelve el ultimo canto tipo envido de la ronda
    """
    def get_ultimo_envido(self):
        return self.ultimo_envido

    """
    Devuelve el ultimo canto tipo truco de la ronda
    """
    def get_ultimo_truco(self):
        return self.ultimo_truco

    def get_cartas_jugadas(self,jugador):
        enfrentamientos = self.get_enfrentamientos()
        cant_jugadores = self.jugadores.count()
        cartas = []
        for i in range(cant_jugadores):
            cartas_jugador = []
            for enfrentamiento in enfrentamientos:
                cartas_jugador.append(enfrentamiento.carta_jugador((jugador.posicion_mesa+i)%cant_jugadores))
            cartas_jugador = [carta for carta in cartas_jugador if carta is not None]
            cartas.append(cartas_jugador)
        return cartas

    def get_ultimo_canto(self):
        result = None
        if self.ultimo_truco:
            result = self.ultimo_truco
        elif self.ultimo_envido:
            result = self.ultimo_envido
        return result

    def se_puede_tirar(self):
        result = True
        ultimo_canto = self.get_ultimo_canto()
        if ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            result = False
        elif self.se_debe_cantar_puntos():
            result = False
        return result

    def se_debe_cantar_puntos(self):
        return (self.ultimo_envido
                and self.ultimo_envido.estado == ACEPTADO
                and not self.ultimo_envido.todos_cantaron())

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
                and not self.ultimo_truco):
            # Termino el primer enfrentamiento y no se ha cantado truco aun
            opciones = [TRUCO, IRSE_AL_MAZO]
        elif not self.ultimo_envido:
            # No se ha cantado envido aun
            opciones = [ENVIDO, REAL_ENVIDO, FALTA_ENVIDO, IRSE_AL_MAZO]
            if self.primer_enfrentamiento and self.primer_enfrentamiento.get_termino():
                # No se puede cantar envido si termina el primer enfrentamiento
                opciones = [IRSE_AL_MAZO]
        else:
            # Ya se ha cantado envido y estamos en el primer enfrentamiento o
            # ya se canto el truco y se respondio
            if self.se_debe_cantar_puntos() and self.ultimo_envido.jugadores.count() > 0:
                opciones.extend([SON_BUENAS])
            elif self.se_debe_cantar_puntos():
                opciones = []
            else:
                opciones = [IRSE_AL_MAZO]
        return opciones

    """
    Devuelve la cantidad de cartas que tiene el jugador adversario.
    """
    def cant_cartas_adversario(self, jugador):
        cant_cartas = [len(i.get_cartas_diponibles()) for i in self.jugadores.all() if i != jugador]
        return cant_cartas[0]

    """
    Calcula de quien es el turno actual segun el estado de la ronda.
    """
    def get_turno(self):
        ultimo_canto = self.get_ultimo_canto()
        ultimo_enfrentamiento = self.get_ultimo_enfrentamiento()
        if self.hay_ganador() and not self.todos_jugadores_listos():
            turno_pos = self.turno_fin_ronda()
        elif ultimo_canto and ultimo_canto.estado == NO_CONTESTADO:
            # Hay un canto que no se contesto aun, el turno es de quien debe responder
            turno_pos = (ultimo_canto.pos_jugador_canto + 1) % self.jugadores.count()
        elif self.se_debe_cantar_puntos():
            turno_pos = (self.mano_pos + self.ultimo_envido.jugadores.count()) % self.jugadores.count()
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
        jugador_en_turno = self.jugadores.get(posicion_mesa = turno_pos)
        return jugador_en_turno

    """
    Reparte cartas a los jugadores.
    """
    def repartir(self):
        cartas_a_repartir = self.mazo.get_n_cartas(self.jugadores.count()*CARTAS_JUGADOR)
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
        if tipo in [ENVIDO, DOBLE_ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]:
            if not self.ultimo_envido:
                canto = Envido(mano_pos=self.mano_pos, puntos_falta=puntos, ronda=self, tipo=tipo)
                canto.pos_jugador_canto = jugador.posicion_mesa
                canto.save()
                self.ultimo_envido = canto
                self.save()
            else:
                canto = self.ultimo_envido
                canto = canto.aumentar(tipo, jugador.posicion_mesa)
                self.ultimo_envido = canto
                self.save()
            canto.mano_pos = self.mano_pos
            canto.save()
        else:
            if tipo in [TRUCO]:
                canto = Truco()
                canto.tipo = tipo
                canto.ronda = self
                canto.pos_jugador_canto = jugador.posicion_mesa
                # Se toma la posicion del jugador para el caso del empate del envido
                canto.mano_pos = self.mano_pos
                canto.save()
                canto.jugadores = self.jugadores.all()
                canto.save()
            else:
                canto = self.get_ultimo_canto().aumentar(tipo,jugador.posicion_mesa)
            self.ultimo_truco = canto
            self.save()
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
        if self.ultimo_truco and self.ultimo_truco.estado == RECHAZADO:
            # Truco cantado y rechazado, por lo tanto ya hay un ganador
            equipo_ganador = self.jugadores.get(
                posicion_mesa=self.ultimo_truco.pos_jugador_canto
                ).equipo
            puntajes[equipo_ganador] += self.ultimo_truco.pts_en_juego
        else:
            # Hay que calcular el ganador de los enfrentamientos
            ganador_enfrentamientos = self.get_ganador_enfrentamientos()
            if self.ultimo_truco:
                # El Truco se canto y acepto, luego hay que definir el ganador
                puntajes[ganador_enfrentamientos] += self.ultimo_truco.pts_en_juego
            else:
                if not self.primer_enfrentamiento and not self.ultimo_envido:
                    # Si el mano no canto envido y se fue en la primer mano
                    puntajes[ganador_enfrentamientos] += 2
                else:
                    puntajes[ganador_enfrentamientos] += 1
        return puntajes

    def calcular_puntos_envido(self):
        puntajes = [0,0]
        if self.ultimo_envido and self.ultimo_envido.estado == RECHAZADO:
            equipo_ganador = self.jugadores.get(posicion_mesa=self.ultimo_envido.pos_jugador_canto).equipo
            puntajes[equipo_ganador] += self.ultimo_envido.pts_en_juego
        elif self.ultimo_envido:
            equipo_ganador = self.ultimo_envido.get_equipo_ganador()
            puntajes[equipo_ganador] += self.ultimo_envido.pts_en_juego
        return puntajes

    def get_enfrentamientos(self):
        enfrentamientos = [self.primer_enfrentamiento,self.segundo_enfrentamiento,self.tercer_enfrentamiento]
        enfrentamientos = [enf for enf in enfrentamientos if enf is not None]
        return enfrentamientos
    """
    Calcula que equipo gano mas enfrentamientos.
    Si hay un empate devuelve el equipo del mano.
    """
    def get_ganador_enfrentamientos(self):
        if self.equipo_mazo >= 0:
            ganador = (self.equipo_mazo + 1 ) % 2
        else:
            enfrentamientos_ganados = [0, 0]
            enfrentamientos = self.get_enfrentamientos()
            for enfrentamiento in enfrentamientos:
                ganador = enfrentamiento.get_ganador()
                if ganador >= 0:
                    # No hubo un empate
                    equipo_ganador = self.jugadores.get(posicion_mesa = ganador).equipo
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
    def irse_al_mazo (self, jugador):
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
        elif self.ultimo_truco and self.ultimo_truco.estado == RECHAZADO:
            # Si no se quizo el truco
            result = True
        elif self.tercer_enfrentamiento and self.tercer_enfrentamiento.get_termino():
            # Se jugaron los 3 enfrentamientos
            result = True
        elif self.segundo_enfrentamiento and not self.tercer_enfrentamiento and self.segundo_enfrentamiento.get_termino():
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

    def todos_jugadores_listos(self):
        return(self.jugadores_listos == self.jugadores.count())

    def jugador_listo(self):
        self.jugadores_listos += 1
        self.save()

    def get_opciones_fin_ronda(self):
        opciones = [SIGUIENTE_RONDA]
        if (self.ultimo_envido
            and self.ultimo_envido.puntos_pedidos
            and not self.ultimo_envido.puntos_mostrados):
            opciones.append(MOSTRAR_PUNTOS)
        elif (self.ultimo_envido
              and self.jugadores_listos==0
              and not self.ultimo_envido.puntos_pedidos
              and self.ultimo_envido.estado == ACEPTADO):
            opciones.append(PEDIR_PUNTOS)
        return opciones

    def turno_fin_ronda(self):
        cant_acciones = self.jugadores_listos
        if self.ultimo_envido and self.ultimo_envido.estado == ACEPTADO and cant_acciones <= 2:
            if self.ultimo_envido.puntos_pedidos:
                cant_acciones +=1
            if self.ultimo_envido.puntos_mostrados:
                cant_acciones +=1
            pos_supuesto_ganador = self.ultimo_envido.get_supuesto_ganador()[0]
            # Solo valido para 2 jugadores
            pos_supuesto_perdedor = (pos_supuesto_ganador + 1) % self.jugadores.count()
            turno_pos = (pos_supuesto_perdedor + cant_acciones) % self.jugadores.count()
        else:
            turno_pos = self.mano_pos + cant_acciones
        return turno_pos

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
    Aumentar crea un nuevo canto de mayor valor, cob
    los puntos que ya estan en juego. Es decir los que le corresponden
    a un jugador si el otro no quiere lo que se canto.
    """
    def aumentar(self, nombre_canto, pos_jugador_canto):
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
    jugadores = models.ManyToManyField(Jugador,through='JugadorEnEnvido',verbose_name='jugadores')
    mano_pos = models.IntegerField(max_length=1)
    puntos_pedidos = models.BooleanField(default=False)
    puntos_mostrados = models.BooleanField(default=False)
    puntos_falta = models.IntegerField(max_length=2,default=0) # Puntos en caso que se gane la falta envido

    """
    Respuestas que tiene un jugador para contestar un envido o derivado
    """
    def get_respuestas(self):
        if self.tipo == str(ENVIDO):
            opciones = [DOBLE_ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]
        elif self.tipo == str(DOBLE_ENVIDO):
            opciones = [REAL_ENVIDO, FALTA_ENVIDO]
        elif self.tipo == str(REAL_ENVIDO):
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

    def get_supuesto_ganador(self):
        puntos_jugadores = []
        for jugador in self.jugadores.all():
            # Agrego a la lista los puntos de los jugadores
            jugador_EnEnvido = jugador.jugadorenenvido_set.get(envido=self)
            puntos_jugadores.append((jugador.posicion_mesa,jugador_EnEnvido.puntos_canto))
        maximo_puntaje = max(puntos_jugadores,key=itemgetter(1))[1]
        # Ganadores son aquellos que tienen el maximo_puntaje
        ganadores = [i for i, j in puntos_jugadores if j == maximo_puntaje]
        # Calculamos la distancia de un jugador al mano pues esto le da prioridad
        distanciasamano = map(self.dist_mano, ganadores)
        minposfrom = distanciasamano.index(min(distanciasamano))
        # El jugador ganador es el mano de los demas ganadores
        ganador_pos = ganadores[minposfrom]
        # El equipo ganador es el equipo del jugador ganador
        maximo_puntaje = maximo_puntaje
        return(ganador_pos,maximo_puntaje)


    """
    Devuelve los puntos cantados por el adversario
    """
    def get_puntos_cantados_oponente(self):
        puntos_oponente = -1
        for jugador in self.jugadores.all():
            # Agrego a la lista los puntos de los jugadores
            if self.ronda.get_turno() != jugador:
                # Se agrega el jugador oponente
                jugador_EnEnvido = jugador.jugadorenenvido_set.get(envido=self)
                puntos_oponente = jugador_EnEnvido.puntos_canto
        return puntos_oponente


    def get_equipo_ganador(self):
        supuesto_ganador = self.get_supuesto_ganador()
        jugador_supuesto_ganador = self.jugadores.get(posicion_mesa=supuesto_ganador[0])
        supuestos_puntos_supuesto_ganador = supuesto_ganador[1]
        equipo_supuesto_ganador = jugador_supuesto_ganador.equipo
        equipo_supuesto_perdedor = (equipo_supuesto_ganador + 1) % 2
        if not self.puntos_pedidos:
            ganador = equipo_supuesto_ganador
        elif not self.puntos_mostrados:
            ganador = equipo_supuesto_perdedor
        else:
            puntos_supuesto_ganador = self.puntos_jugador(jugador_supuesto_ganador)
            if puntos_supuesto_ganador == supuestos_puntos_supuesto_ganador:
                ganador = equipo_supuesto_ganador
            else:
                ganador = equipo_supuesto_perdedor
        return ganador

    def cantar_puntos(self,jugador,puntos):
        jugadorEnEnvido = JugadorEnEnvido(jugador=jugador,
                                          envido=self,
                                          puntos_canto=puntos)
        jugadorEnEnvido.save()


    def todos_cantaron(self):
        return self.jugadores.count() == 2


    def aumentar(self, tipo, pos_jugador_canto):
        self.aceptar()
        self.save()
        canto = Envido(puntos_falta=self.puntos_falta, ronda=self.ronda,
                       pos_jugador_canto=pos_jugador_canto, pts_en_juego=self.pts_en_juego, 
                       tipo=tipo)
        canto.save()
        return canto

    def aceptar(self):
        self.estado = ACEPTADO
        if self.tipo == str(FALTA_ENVIDO):
            self.pts_en_juego = self.puntos_falta
        elif self.tipo ==  str(ENVIDO):
            self.pts_en_juego += 1
        elif self.tipo == str(DOBLE_ENVIDO):
            self.pts_en_juego += 2
        else:
            if self.pts_en_juego > 1:
                # Si se canta real envido con otro canto antes
                self.pts_en_juego += 3
            else:
                self.pts_en_juego += 2
        self.save()


    def pedir_puntos(self):
        self.puntos_pedidos = True
        self.save()

    def mostrar_puntos(self):
        self.puntos_mostrados = True
        self.save()

class JugadorEnEnvido(models.Model):
    jugador = models.ForeignKey(Jugador,verbose_name='jugador')
    envido = models.ForeignKey(Envido,verbose_name='envido')
    puntos_canto = models.IntegerField(max_length=2,null=True)

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
