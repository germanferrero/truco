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
                                        password='asdf',)
        user1.save()
        user2 = User.objects.create_user(username='test_user2',email='email2@email.com',
                                        password='asdf',)
        user2.save()
        user3 = User.objects.create_user(username='test_user3',email='email3@email.com',
                                        password='asdf',)
        user3.save()
        lobby = Lobby()
        #Creo partidas
        partida1 = lobby.crear_partida(user=user1, nombre = 'Partida1 a 15 sin password',
                                    puntos_objetivo=15,password='')
        partida1.save()
        partida2 = lobby.crear_partida(user=user1, nombre = 'Partida2 a 30 sin password',
                                    puntos_objetivo=15,password='')
        partida2.save()
        partida3 = lobby.crear_partida(user=user1, nombre = 'Partida3 a 30 sin password con dos jugadores',
                                    puntos_objetivo=15,password='')
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
                    nombre_carta = str(numero)+" "+ 'de' + "" + str(palo_carta)
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
#        print '[%s]' % ', '.join(map(str, list(Carta.objects.all())))

    """
    Test que se fija que una partida creada tiene seteado el estado en "EN_ESPERA".
    Luego agrega un jugador nuevo a la partida y testea que se cambie el estado a "EN_CURSO"'''
    """
    def test_estado_partidas(self):
        lobby = Lobby()
        partida = Partida.objects.get(nombre ='Partida1 a 15 sin password')
        # Usuario para agregar a la partida
        user2 = User.objects.get(username ='test_user2')
        # Obtengo los jugadores de la partida
        jugadores =  list(partida.jugadores.all())
        # La partida esta en espera hasta que se una un nuevo jugador
        self.assertEqual(partida.estado, EN_ESPERA)
        #Agrego un nuevo jugador
        lobby.unirse_partida(user2, partida)
        # Seteo el estado de la partida
        partida.actualizar_estado()
        # La partida debe estar en curso una vez que tenga dos jugadores
        self.assertEqual(partida.estado, EN_CURSO)



    # Test que verifica que la lista de partidas disponibles se cree cuando se crea
    # una nueva partida, pero que deje de estar cuando se haya unido un jugador a la partida"""
    def test_listas_partidas(self):
        ''        #Creo una lista para compararla con la real
        lista_partidas = [] 
        lobby = Lobby()
        partida1 = Partida.objects.get(nombre = 'Partida1 a 15 sin password')
        partida2 = Partida.objects.get(nombre = 'Partida2 a 30 sin password')
        user2 = User.objects.get(username ='test_user2')
        user3 = User.objects.get(username = 'test_user3')
        # Agrego las partidas a la partida para compraralas luego
        lista_partidas.append(partida1)
        lista_partidas.append(partida2)
        # Me fijo que esten las dos partidas
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))
        # Agrego a un jugador a la partida uno, por lo tanto debe salir de la lista disponibles
        lobby.unirse_partida(user2, partida1)
        # Actualizo el estado de la partida
        partida1.actualizar_estado()
        # Lo remuevo de la lista auxiliar
        lista_partidas.remove(partida1)
        # Compruebo que no esta en la lista de partidas en espera
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))
        # Agrego un jugador a la partida 2
        lobby.unirse_partida(user2, partida2)
        # Actualizo el estado de la partida
        partida2.actualizar_estado()
        # Lo remuevo de la lista auxiliar
        lista_partidas.remove(partida2)
        # Compruebo que no esta en la lista de partidas en espera
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))


    def test_crear_ronda(self):
        user2 = User.objects.get(username='test_user2')
        partida = Partida.objects.get(nombre = 'Partida1 a 15 sin password')
        lobby = Lobby()
        # Agrego a un jugador a la partida
        lobby.unirse_partida(user2, partida)
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
        # Chequeo que la mano sea el que esta en la posicion 0 (El que creo la partida)
        self.assertEqual(ronda.mano_pos, 0)
        # Obtengo la ultima ronda
        ronda = partida.get_ronda_actual()
        # Obtengo las opciones que tengo para cantar
        opciones = ronda.get_opciones()
        # Chequeo que la opcion que este disponible sea solo cantar envido
        self.assertEqual(opciones[0], ENVIDO)

    """
    Verifica que los puntos cuando se canta truco se sumen correctamente
    """
    def test_truco_simple(self):
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        # Se canta y acepta un truco simple
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # verificamos que se le den los 2 puntos al jugador que gano
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores)
        if ganador == jugador1:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugador1:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        self.assertEqual(puntaje_despues, puntaje_antes + 2)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        puntaje = partida.puntos_e1
        # Se canta y se rechaza un truco simple
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.rechazar()
        # Si se rechaza corresponde 1 punto para el otro jugador
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        self.assertEqual(partida.puntos_e1, puntaje + 1)

    """
    Verifica que los puntos cuando se canta retruco o vale cuatro se sumen correctamente
    """
    def test_truco_retruco_y_valecuatro(self):
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        # Se canta truco, se responde retruco y se acepta
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(RETRUCO, jugador2, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # verificamos que se le den los 3 puntos al jugador que gano
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores)
        if ganador == jugador1:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugador1:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        self.assertEqual(puntaje_despues, puntaje_antes + 3)
         # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        puntaje = partida.puntos_e2
        # Se canta truco, se responde retruco y se rechaza
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(RETRUCO, jugador2, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.rechazar()
        # Si se rechaza corresponde 2 punto para el otro jugador
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        self.assertEqual(partida.puntos_e2, puntaje + 2)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        # Se canta truco, se responde retruco y vale cuatro y se acepta
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(RETRUCO, jugador2, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(VALE_CUATRO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.aceptar()
        # verificamos que se le den los 4 puntos al jugador que gano
        puntaje1 = partida.puntos_e1
        puntaje2 = partida.puntos_e2
        ganador = self.aux_truco_terminar_ronda(ronda, jugadores)
        if ganador == jugador1:  # Puntos antes de terminar la ronda
            puntaje_antes = puntaje1
        else:
            puntaje_antes = puntaje2
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        if ganador == jugador1:  # Puntos despues de terminar la ronda
            puntaje_despues = partida.puntos_e1
        else:
            puntaje_despues = partida.puntos_e2
        self.assertEqual(puntaje_despues, puntaje_antes + 4)
        # Nueva ronda
        ronda, partida, jugadores = self.aux_truco_nueva_ronda()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        puntaje = partida.puntos_e1
        # Se canta truco, se responde retruco y vale cuatro y se rechaza
        ronda.crear_canto(TRUCO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(RETRUCO, jugador2, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        ronda.crear_canto(VALE_CUATRO, jugador1, partida.get_min_pts_restantes())
        canto = ronda.get_ultimo_canto()
        canto.rechazar()
        # Si se rechaza corresponde 3 punto para el otro jugador
        partida.actualizar_puntajes()  # Se actualizan los puntajes de la ronda
        self.assertEqual(partida.puntos_e1, puntaje + 3)

    """
    Funcion auxiliar de los test del canto truco. Crea una nueva ronda con dos
    jugadores que han tirado cada uno una carta.
    """
    def aux_truco_nueva_ronda(self):
        # Configuramos una partida donde se termino el primer enfrentamiento
        partida = Partida.objects.get(nombre = 'Partida3 a 30 sin password con dos jugadores')
        partida.crear_ronda()
        # La partida ya esta lista para que los jugadores tiren las cartas
        jugadores = partida.jugadores.all()
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        ronda = partida.get_ronda_actual()
        carta1 = jugador1.cartas_disponibles.order_by('?')[0]
        carta2 = jugador2.cartas_disponibles.order_by('?')[0]
        # Se tiran dos cartas aleatoriamente, una por cada jugador
        enfrentamiento = ronda.crear_enfrentamiento(jugador1)
        enfrentamiento.agregar_carta(carta1)
        enfrentamiento.agregar_carta(carta2)
        return (ronda, partida, jugadores)

    """
    Funcion auxiliar de los test del canto truco. Termina la ronda tirando todas
    las cartas restantes de los jugadores.
    """
    def aux_truco_terminar_ronda(self, ronda, jugadores):
        jugador1 = jugadores[0]
        jugador2 = jugadores[1]
        # Tomanos una carta al azar de cada jugador
        carta1 = jugador1.cartas_disponibles.order_by('?')[0]
        carta2 = jugador2.cartas_disponibles.order_by('?')[0]
        # Cada jugador "tira" la carta
        enfrentamiento = ronda.crear_enfrentamiento(jugador1)
        enfrentamiento.agregar_carta(carta1)
        enfrentamiento.agregar_carta(carta2)
        # Tomanos una carta al azar de cada jugador
        carta1 = jugador1.cartas_disponibles.order_by('?')[0]
        carta2 = jugador2.cartas_disponibles.order_by('?')[0]
        # Cada jugador "tira" la carta
        enfrentamiento = ronda.crear_enfrentamiento(jugador1)
        enfrentamiento.agregar_carta(carta1)
        enfrentamiento.agregar_carta(carta2)
        # Si hay tres enfrentamientos hay un ganador necesariamente
        ganador_pos = ronda.get_ganador_enfrentamientos()
        ganador = jugadores.get(posicion_mesa=ganador_pos)
        # Se devuelve el objeto jugador que corresponde al ganador de los enfrentamientos
        return ganador

    """
    Verifica que los puntos que se suman a cada jugador al final de la ronda
    sean los correspondientes al envido cantado durante la misma.
    """
    #def test_envido_puntos (self):
        #partida = Partida.objects.get(nombre = 'Partida3 a 30 sin password con dos jugadores')
        ## Obtengo los jugadores
        #jugadores = partida.jugadores.all()
        #ronda = self.aux_envido_nueva_ronda(partida)
        ## Creo un canto envido
        #ronda.crear_canto(ENVIDO, jugadores[0], partida.get_min_pts_restantes())
        #opciones = ronda.get_opciones()
        ## Verificamos las opciones disponibles
        #self.assertTrue(QUIERO in opciones)
        #self.assertTrue(NO_QUIERO in opciones)
        #self.assertTrue(DOBLE_ENVIDO in opciones)
        #self.assertTrue(REAL_ENVIDO in opciones)
        #self.assertTrue(FALTA_ENVIDO in opciones)
        ## Obtengo el ultimo canto
        #canto = ronda.get_ultimo_canto()
        #self.assertEqual(canto.pts_en_juego,1)
        #canto.aceptar()
        ## Obtengo el ganador
        #canto.get_ganador()
        #puntos_jugador1 = canto.puntos_jugador(jugadores[0])
        #puntos_jugador2 = canto.puntos_jugador(jugadores[1])
        #if puntos_jugador1 < puntos_jugador2:
            #self.assertEqual(canto.maximo_puntaje, puntos_jugador2)
        #else:
            #self.assertEqual(canto.maximo_puntaje, puntos_jugador1)

    #def test_envido_turno(self):
        #pass

    #"""
    #Se verifica que en las opciones restantes de la partida queden las que
    #corresponden, respecto al envido, segun el canto que este en juego.
    #"""
    #def test_envido_opciones(self):
        #partida = Partida.objects.get(nombre = 'Partida3 a 30 sin password con dos jugadores')
        ## Obtengo los jugadores
        #jugadores = partida.jugadores.all()
        #ronda = self.aux_envido_nueva_ronda(partida)
        ## Se canta envido
        #ronda.crear_canto(ENVIDO, jugadores[0], partida.get_min_pts_restantes())
        #ronda.save()
        #canto = ronda.get_ultimo_canto()
        #canto.save()
        #opciones = ronda.get_opciones()
        ## Verificamos las opciones disponibles
        #self.assertTrue(QUIERO in opciones)
        #self.assertTrue(NO_QUIERO in opciones)
        ##self.assertTrue(DOBLE_ENVIDO in opciones)
        #self.assertTrue(REAL_ENVIDO in opciones)
        #self.assertTrue(FALTA_ENVIDO in opciones)
        ## Se responde envido (se juega un doble envido)
        #ronda.crear_canto(DOBLE_ENVIDO, jugadores[1], partida.get_min_pts_restantes())
        #opciones = ronda.get_opciones()
        #self.assertTrue(QUIERO in opciones)
        #self.assertTrue(NO_QUIERO in opciones)
        #self.assertTrue(REAL_ENVIDO in opciones)
        #self.assertTrue(FALTA_ENVIDO in opciones)
        ## Se responde real envido
        #ronda.crear_canto(REAL_ENVIDO, jugadores[0], partida.get_min_pts_restantes())
        #opciones = ronda.get_opciones()
        #self.assertTrue(QUIERO in opciones)
        #self.assertTrue(NO_QUIERO in opciones)
        #self.assertTrue(FALTA_ENVIDO in opciones)
        ## Se responde falta envido
        #ronda.crear_canto(FALTA_ENVIDO, jugadores[1], partida.get_min_pts_restantes())
        #opciones = ronda.get_opciones()
        #self.assertTrue(QUIERO in opciones)
        #self.assertTrue(NO_QUIERO in opciones)


    #def aux_envido_nueva_ronda(self, partida):
        ## La partida debe estar lista para crear una ronda
        #if partida.is_ready():
            ##Creo una ronda en la partida
            #ronda = partida.crear_ronda()
            #ronda.save()
        ## Obtengo la ultima ronda
        #ronda = partida.get_ronda_actual()
        #return ronda
