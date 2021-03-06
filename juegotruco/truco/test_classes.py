from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from truco.constants import *
from truco.models import *

class TrucoTests(TestCase):

    def setUp(self):
        # Creo usuarios
        user1 = User.objects.create_user(username='test_user1', email='email@email.com',
                                        password='asdf',)
        user1.save()
        user2 = User.objects.create_user(username='test_user2',email='email2@email.com',
                                        password='asdf',)
        user2.save()
        #Creo un lobby
        lobby = Lobby()
        #Creo una partida
        partida3 = lobby.crear_partida(user=user1, nombre = 'Partida con dos jugadores',
                                    puntos_objetivo=15, cantidad_jugadores=2)
        partida3.save()
        # Agrego a un jugador a la partida
        lobby.unirse_partida(user2, partida3)
        # Actualizo el estado de la partida
        partida3.actualizar_estado()
        #Creo las cartas
        valor_otro = 7
        for palo_carta in range(1,5):
            for numero in range (1,13):
                if numero!=8 and numero!=9:
                    nombre_carta = str(numero)+" "+ 'de' + " " + str(palo_carta)
                    if nombre_carta == "1 de 1":
                        valor_jer = 1
                    elif nombre_carta == '1 de 2':
                        valor_jer = 2
                    elif nombre_carta == '7 de 1':
                        valor_jer = 3
                    elif nombre_carta == '7 de 3':
                        valor_jer = 4
                    else :
                        valor_jer = valor_otro
                    if numero == 10 or numero == 11 or numero == 12:
                        envido = 0
                    else:
                        envido = numero
                    carta = Carta.objects.create(nombre = nombre_carta, valor_jerarquico = valor_jer,
                                            valor_envido = envido, palo = palo_carta, imagen = nombre_carta)
                    carta.save()
                    valor_otro = valor_otro-1
                    if valor_otro == 4:
                        valor_otro = 14
        #        print len(list(Carta.objects.all()))
        #         print '[%s]' % ', '.join(map(str, list(Carta.objects.all())))

        """
    Test que verifica los metodos de la clase lobby
    """
    def test_class_Lobby(self):
        # Obtengo los usuarios
        user1 = User.objects.get(username ='test_user1')
        user2 = User.objects.get(username ='test_user2')
        # Creo un lobby
        lobby = Lobby()
        # Obtengo la lista de partidas
        lista_partidas = list(lobby.get_lista_partidas())
        # Verifico que la lista este vacia por lo tanto no debe haber partidas
        self.assertEqual(lista_partidas,[])
        # Creo una nueva partida
        partida = lobby.crear_partida(user=user1, nombre = 'partida a 15',
                                    puntos_objetivo=15, cantidad_jugadores=2)
        # Obtengo la lista de partidas
        lista_partidas = list(lobby.get_lista_partidas())
        # Verifico que se haya agregado la partida
        self.assertEqual(str(lista_partidas),"[<Partida: partida a 15>]")
        # Agrego al mismo jugador a la partida
        result = lobby.unirse_partida(user1, partida)
        # Verifico que no se haya agragado
        self.assertEqual(result,-1)
        # Agrego otro jugador a la partida
        result = lobby.unirse_partida(user2, partida)
        # Verifico que se haya agragado
        self.assertEqual(result,0)
        # Seteo el estado de la partida
        partida.actualizar_estado()
        # Obtengo la lista de partidas
        lista_partidas = list(lobby.get_lista_partidas())
        # Verifico que la partida ya no este disponible
        self.assertEqual(lista_partidas,[])

    """
    Test que verifica todos los metodos de la clase partida
    """
    def test_class_partida(self):
        # Obtengo los usuarios
        user1 = User.objects.get(username ='test_user1')
        user2 = User.objects.get(username ='test_user2')
        # Creo un lobby
        lobby = Lobby()
        #Creo una partida
        partida = lobby.crear_partida(user=user1, nombre = 'Partida a 30',
                                    puntos_objetivo=30, cantidad_jugadores=2)
        # Agrego un jugador a la partida
        lobby.unirse_partida(user2, partida)
        # Seteo el estado de la partida
        partida.actualizar_estado()
        # Verifico que el estado sea EN_CURSO
        self.assertEqual(partida.estado,EN_CURSO)
        # Verifico que la partida esta lista para crear una nueva ronda,
        # osea is_ready debe devolver True
        self.assertEqual(partida.is_ready(), True)
        # Creo una nueva ronda
        ronda = partida.crear_ronda()
        # Se verifica si ronda_actual sea igual a ronda
        self.assertEqual(partida.ronda_actual,ronda)
        # Verifico que la partida no esta lista para crear una nueva ronda,
        # osea is_ready debe devolver false
        self.assertEqual(partida.is_ready(), False)
        # Le asigno a los jugadores puntajes
        partida.puntos_e1 = 3
        partida.puntos_e2 = 5
        # Obtengo el puntajes de los usuarios con get_puntajes
        puntajes= partida.get_puntajes(user1)
        # Verifico que cada equipo tenga el puntaje que corresponde a lo asiganado
        self.assertEqual(puntajes[0],3)
        self.assertEqual(puntajes[1],5)
        # Verifico que get_ganador no de un ganador
        self.assertEqual(partida.get_ganador(), -1)
        # Cambio la mano, ahora deberia ser el jugador que se unio a la partida
        partida.actualizar_mano()
        #Verifico que sea el jugador de la posicion 1
        self.assertEqual(partida.mano_pos,1)
        # Verifico que lo puntos si se cantara falta envido sean 10
        self.assertEqual(partida.get_min_pts_restantes(), 10)
        # Le asigno al equipo 2 los puntos objetivos
        partida.puntos_e2 = 30
        # Verifico que get_ganador me de como ganador al equipo 2 
        # (que seria equipo1s segun como lo programamos)
        self.assertEqual(partida.get_ganador(), 1)

########TESTS DE CLASE RONDA########
    """
    Test que verifica que el metodo devuelva bien las cartas que hayan jugado
    """
    def test_get_cartas_jugadas(self):
        cartas_tiradas = []
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        # Obtengo las cartas de los jugadores
        carta1 = jugador1.get_cartas_disponibles()
        carta2 = jugador2.get_cartas_disponibles()
        # Creo un enfrentamiento
        enfrentamiento = ronda.crear_enfrentamiento(jugador1)
        # Elijo la primera carta
        carta_j1 = carta1[0]
        cartas_tiradas.append ([carta1[0]])
        cartas_tiradas.append([])
        # Agrego una carta al enfrentamiento 
        enfrentamiento.agregar_carta(carta_j1)
        # Hago el get
        cartas_tiradas_del_get = ronda.get_cartas_jugadas(jugador1)
        # Verifico que devuelva bien las cartas
        self.assertEqual(cartas_tiradas, cartas_tiradas_del_get)
        # Elijo una carta del jugador 2
        cartas_tiradas = []
        carta_j2 = carta2[0]
        cartas_tiradas.append([carta2[0]])
        cartas_tiradas.append([carta1[0]])
        # Agrego una carta al enfrentamiento 
        enfrentamiento.agregar_carta(carta_j2)
        # Hago el get
        cartas_tiradas_del_get = ronda.get_cartas_jugadas(jugador2)
        # Verifico que devuelva bien las cartas
        self.assertEqual(cartas_tiradas, cartas_tiradas_del_get)

    """
    Test que verifica que la funcion devuelve el ultimo canto que este en juego
    """
    def test_get_ultimo_canto(self):
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        ronda.crear_canto(ENVIDO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto, ronda.ultimo_envido())
        ronda.crear_canto(TRUCO, jugador1, 3)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto, ronda.ultimo_truco())

    """
    Test que verifica que se pueda tirar solo cuando ya no haya un canto
    """
    def test_se_puede_tirar(self):
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        result = ronda.se_puede_tirar()
        self.assertEqual(True, result)
        ronda.crear_canto(ENVIDO, jugador1, 10)
        result = ronda.se_puede_tirar()
        self.assertEqual(False, result)

#######Test clase canto#######
    """
    Test que verifica que se acepte los cantos en envido y en el truco
    """
    def test_canto_aceptar(self):
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        #Aceptar un canto de tipo envido
        ronda.crear_canto(REAL_ENVIDO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto.estado, NO_CONTESTADO)
        canto.aceptar()
        self.assertEqual(canto.estado, ACEPTADO)
        #Aceptar un canto de tipo truco
        ronda.crear_canto(TRUCO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto.estado, NO_CONTESTADO)
        canto.aceptar()
        self.assertEqual(canto.estado, ACEPTADO)

    """
    Test que verifica que se acepten los cantos en envido y en el truco
    """
    def test_canto_rechazar(self):
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        #Rechazar un canto de tipo envido
        ronda.crear_canto(ENVIDO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto.estado, NO_CONTESTADO)
        canto.rechazar()
        self.assertEqual(canto.estado, RECHAZADO)
        #Rechazar un canto de tipo truco
        ronda.crear_canto(TRUCO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        self.assertEqual(canto.estado, NO_CONTESTADO)
        canto.aceptar()
        self.assertEqual(canto.estado, ACEPTADO)

#######Test clase envido#######
    """
    Test que verifica que no se deban cantar los puntos antes de cantar aceptar 
    el envido, y luego si
    """
    def test_se_debe_cantar_puntos(self):
        # Obtengo una partida con dos jugadores y una ronda ya creada
        partida = Partida.objects.get(nombre= "Partida con dos jugadores")
        # Obtengo la ronda actual
        ronda = partida.crear_ronda()
        # Obtengo los jugadores
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        result = ronda.se_debe_cantar_puntos()
        self.assertEqual(None, result)
        ronda.crear_canto(ENVIDO, jugador1, 10)
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        result = ronda.se_debe_cantar_puntos()
        self.assertEqual(True, result)