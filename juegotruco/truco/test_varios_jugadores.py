from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from truco.constants import *
from truco.models import *


class TrucoTests(TestCase):

    """
    Creamos nuevos elementos en la base de datos para hacer los tests
    """
    def setUp(self):
        #Creo usuarios
        user1 = User.objects.create_user(username='test_user1', email='email@email.com',
                                         password='asdf', )
        user1.save()
        user2 = User.objects.create_user(username='test_user2', email='email2@email.com',
                                         password='asdf', )
        user2.save()
        user3 = User.objects.create_user(username='test_user3', email='email3@email.com',
                                         password='asdf', )
        user3.save()
        user4 = User.objects.create_user(username='test_user4', email='email4@email.com',
                                         password='asdf', )
        user4.save()
        user5 = User.objects.create_user(username='test_user5', email='email5@email.com',
                                         password='asdf', )
        user5.save()
        user6 = User.objects.create_user(username='test_user6', email='email6@email.com',
                                         password='asdf', )
        user6.save()
        lobby = Lobby()
        #Creo partidas
        partida1 = lobby.crear_partida(user=user1, nombre='Partida1 a 15 para 4 jugadores con un usuario',
                                       puntos_objetivo=15, cantidad_jugadores=4)
        partida1.save()
        partida2 = lobby.crear_partida(user=user1, nombre='Partida2 a 30 con 4 jugadores',
                                       puntos_objetivo=15, cantidad_jugadores=4)
        # Agrego jugadores a la partida
        lobby.unirse_partida(user2, partida2)
        lobby.unirse_partida(user3, partida2)
        lobby.unirse_partida(user4, partida2)
        partida2.save()
        # Actualizo el estado de la partida
        partida2.actualizar_estado()
        partida3 = lobby.crear_partida(user=user1, nombre='Partida3 a 30 con 6 jugadores',
                                       puntos_objetivo=15, cantidad_jugadores=6)
        partida3.save()
        # Agrego jugadores a la partida
        lobby.unirse_partida(user2, partida3)
        lobby.unirse_partida(user3, partida3)
        lobby.unirse_partida(user4, partida3)
        lobby.unirse_partida(user5, partida3)
        lobby.unirse_partida(user6, partida3)
        # Actualizo el estado de la partida
        partida3.actualizar_estado()

        #Creo las cartas
        valor_otro = 7
        for palo_carta in range(1, 5):
            for numero in range(1, 13):
                if numero != 8 and numero != 9:
                    nombre_carta = str(numero) + " " + 'de' + "" + str(palo_carta)
                    if nombre_carta == "1 de 1":
                        valor_jer = 1
                    elif nombre_carta == '1 de 2':
                        valor_jer = 2
                    elif nombre_carta == '7 de 1':
                        valor_jer = 3
                    elif nombre_carta == '7 de 3':
                        valor_jer = 4
                    else:
                        valor_jer = valor_otro
                    if numero == 10 or numero == 11 or numero == 12:
                        envido = 0
                    else:
                        envido = numero
                    carta = Carta.objects.create(nombre=nombre_carta, valor_jerarquico=valor_jer,
                                                 valor_envido=envido, palo=palo_carta, imagen=nombre_carta)
                    carta.save()
                    valor_otro = valor_otro-1
                    if valor_otro == 4:
                        valor_otro = 14

    """
    Test que verifica que la lista de partidas disponibles se cree cuando se crea
    una nueva partida, pero que deje de estar cuando se hayan unido todos los jugadores a la partida
    """
    def test_listas_partidas(self):
        #Creo una lista para compararla con la real
        lista_partidas = []
        lobby = Lobby()
        partida = Partida.objects.get(nombre='Partida1 a 15 para 4 jugadores con un usuario')
        user1 = User.objects.get(username='test_user1')
        user2 = User.objects.get(username='test_user2')
        user3 = User.objects.get(username='test_user3')
        user4 = User.objects.get(username='test_user4')
        # Agrego las partidas a la partida para compraralas luego
        lista_partidas.append(partida)
        # Me fijo que esten las dos partidas
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))
        # Agrego losjugadores a la partida, por lo tanto debe salir de la lista disponibles
        lobby.unirse_partida(user2, partida)
        lobby.unirse_partida(user3, partida)
        lobby.unirse_partida(user4, partida)
        # Actualizo el estado de la partida
        partida.actualizar_estado()
        # Lo remuevo de la lista auxiliar
        lista_partidas.remove(partida)
        # Compruebo que no esta en la lista de partidas en espera
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))

    """
    Test que se fija que una partida creada tiene seteado el estado en "EN_ESPERA".
    Luego agrega un jugador nuevo a la partida y testea que se cambie el estado a "EN_CURSO"'''
    """
    def test_estado_partidas(self):
        lobby = Lobby()
        partida = Partida.objects.get(nombre='Partida1 a 15 para 4 jugadores con un usuario')
        # Usuarios para agregar a la partida
        user2 = User.objects.get(username='test_user2')
        user3 = User.objects.get(username='test_user3')
        user4 = User.objects.get(username='test_user4')
        # La partida esta en espera hasta que se una un nuevo jugador
        self.assertEqual(partida.estado, EN_ESPERA)
        #Agrego un nuevo jugador
        lobby.unirse_partida(user2, partida)
        lobby.unirse_partida(user3, partida)
        lobby.unirse_partida(user4, partida)
        # Seteo el estado de la partida
        partida.actualizar_estado()
        # La partida debe estar en curso una vez que tenga dos jugadores
        self.assertEqual(partida.estado, EN_CURSO)

    def test_crear_ronda(self):
        user2 = User.objects.get(username='test_user2')
        user3 = User.objects.get(username='test_user3')
        user4 = User.objects.get(username='test_user4')
        partida = Partida.objects.get(nombre='Partida1 a 15 para 4 jugadores con un usuario')
        lobby = Lobby()
        # Agrego los jugadores a la partida
        lobby.unirse_partida(user2, partida)
        lobby.unirse_partida(user3, partida)
        lobby.unirse_partida(user4, partida)
        # Actualizo el estado de la partida
        partida.actualizar_estado()
        # La partida debe estar lista para crear una ronda
        self.assertTrue(partida.is_ready())
        #Creo una ronda en la partida
        ronda = partida.crear_ronda()
        # Testeo que se haya creado una ronda
        self.assertNotEqual(list(partida.ronda_set.all()), [])
        # Obtengo los jugadores
        jugadores = list(partida.jugadores.all())
        # Chequeo que se les hayan asignado 3 cartas a cada uno
        self.assertEqual(len((jugadores[0].cartas.all())), 3)
        self.assertEqual(len((jugadores[1].cartas.all())), 3)
        self.assertEqual(len((jugadores[2].cartas.all())), 3)
        self.assertEqual(len((jugadores[3].cartas.all())), 3)
        # Chequeo que la mano sea el que esta en la posicion 0 (El que creo la partida)
        self.assertEqual(ronda.mano_pos, 0)
        # Obtengo la ultima ronda
        ronda = partida.get_ronda_actual()
        # Obtengo las opciones que tengo para cantar
        opciones = ronda.get_opciones()
        # Chequeo que la opcion que este disponible sea solo cantar envido
        self.assertTrue(ENVIDO in opciones)
        self.assertTrue(REAL_ENVIDO in opciones)
        self.assertTrue(FALTA_ENVIDO in opciones)
        self.assertTrue(IRSE_AL_MAZO in opciones)

    """
    Verifica que los puntos cuando se canta retruco o vale cuatro se sumen correctamente
    """
    def test_truco_retruco_y_valecuatro(self):
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        # Se canta truco, se responde retruco y se acepta
        ronda.crear_canto(TRUCO, jugadores[0], partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aumentar(RETRUCO, jugadores[4].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # Obtenemos los puntajes antes y despues de la ronda
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores, partida)
        if ganador == jugadores[0].equipo:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugadores[0].equipo:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        # Verificamos que se le den los 3 puntos al gandor del retruco
        self.assertEqual(puntaje_despues, puntaje_antes + 3)
         # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        puntaje = partida.puntos_e2
        # Se canta truco, se responde retruco y se rechaza
        ronda.crear_canto(TRUCO, jugadores[0], partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aumentar(RETRUCO, jugadores[5].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.rechazar()
        # Si se rechaza corresponde 2 punto para el otro jugador
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        self.assertEqual(partida.puntos_e2, puntaje + 2)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        # Se canta truco, se responde retruco y vale cuatro y se acepta
        ronda.crear_canto(TRUCO, jugadores[0], partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aumentar(RETRUCO, jugadores[4].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.aumentar(VALE_CUATRO, jugadores[5].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # Obtenemos los puntajes antes y despues de la ronda
        puntaje1 = partida.puntos_e1
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores, partida)
        if ganador == jugadores[0].equipo:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugadores[0].equipo:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        # verificamos que se le den los 4 puntos al ganador del vale cuatro
        self.assertEqual(puntaje_despues, puntaje_antes + 4)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        puntaje = partida.puntos_e1
        # Se canta truco, se responde retruco y vale cuatro y se rechaza
        ronda.crear_canto(TRUCO, jugadores[0], partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aumentar(RETRUCO, jugadores[5].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.aumentar(VALE_CUATRO, jugadores[4].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.rechazar()
        # Si se rechaza corresponde 3 punto para el otro jugador
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        self.assertEqual(partida.puntos_e1, puntaje + 3)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        # Se canta truco, se responde retruco y se canta el vale cuatro luego de que se haya aceptado
        ronda.crear_canto(TRUCO, jugadores[0], partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aumentar(RETRUCO, jugadores[4].posicion_mesa)
        canto.aceptar() # El equipo 1 acepta el retruco
        canto = ronda.get_ultimo_canto()
        # El equipo 1 recanta vale cuatro
        canto.aumentar(VALE_CUATRO, jugadores[5].posicion_mesa)
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # verificamos que se le den los 4 puntos al jugador que gano
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores, partida)
        if ganador == jugadores[0].equipo:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugadores[0].equipo:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        self.assertEqual(puntaje_despues, puntaje_antes + 4)

    """
    Funcion auxiliar que dada la pocision en mesa del jugador devuelve el jugador.
    """
    def aux_jugador_en_mesa(self, pos_mesa, partida):
        return partida.jugadores.get(posicion_mesa=pos_mesa)
        
    """
    Funcion auxiliar de los test del canto truco. Crea una nueva ronda con dos
    jugadores que han tirado cada uno una carta.
    """
    def aux_truco_nueva_ronda(self):
        # Configuramos una partida donde se termino el primer enfrentamiento
        partida = Partida.objects.get(nombre='Partida3 a 30 con 6 jugadores')
        partida.crear_ronda()
        # La partida ya esta lista para que los jugadores tiren las cartas
        jugadores = partida.jugadores.all()
        # Guardamos los jugadores en una lista ordenada segun su pocision en la mesa
        lista_jugadores = []
        for pos_mesa in range(partida.cantidad_jugadores):
            lista_jugadores.append(self.aux_jugador_en_mesa(pos_mesa, partida))
        ronda = partida.get_ronda_actual()
        # Cada jugador tira una carta aleatoriamente
        enfrentamiento = ronda.crear_enfrentamiento(self.aux_jugador_en_mesa(0, partida))
        for jugador in jugadores:
            enfrentamiento.agregar_carta(jugador.cartas_disponibles.order_by('?')[0])
        return (ronda, partida, lista_jugadores)

    """
    Funcion auxiliar de los test del canto truco. Termina la ronda tirando todas
    las cartas restantes de los jugadores.
    """
    def aux_truco_terminar_ronda(self, ronda, jugadores, partida):
        # Hacemos que los jugadores tiren las 2 cartas que le quedan
        enfrentamiento = ronda.crear_enfrentamiento(self.aux_jugador_en_mesa(0, partida))
        for jugador in jugadores:
            enfrentamiento.agregar_carta(jugador.cartas_disponibles.order_by('?')[1])
        ganador_pos = ronda.get_ganador_enfrentamientos()
        if ganador_pos < 0:
            for jugador in jugadores:
                enfrentamiento.agregar_carta(jugador.cartas_disponibles.order_by('?')[2])
            ganador_pos = ronda.get_ganador_enfrentamientos()
        ganador = self.aux_jugador_en_mesa(ganador_pos, partida)
        # Si hay tres enfrentamientos hay un ganador necesariamente
        # Se devuelve el objeto jugador que corresponde al ganador de los enfrentamientos
        return ganador.equipo
