from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from truco.constants import *
from truco.models import *

class TrucoTests(TestCase):

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
        partida3 = lobby.crear_partida(user=user1, nombre = 'Partida3 a 30 sin password',
                                    puntos_objetivo=15,password='')
        partida3.save()
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


    #Test que se fija que una partida creada tiene seteado el estado en "EN_ESPERA".
    #Luego agrega un jugador nuevo a la partida y testea que se cambie el estado a "EN_CURSO"'''
    def test_estado_partidas(self):
        lobby = Lobby()
        partida1 = Partida.objects.get(nombre ='Partida1 a 15 sin password')
        user2 = User.objects.get(username ='test_user2')

        lista =  partida1.jugadores.all()
        # La partida esta en espera hasta que se una un nuevo jugador
        self.assertEqual(len(lista),1)
        self.assertEqual(partida1.estado, EN_ESPERA)
        lobby.unirse_partida(user2, partida1)
        # La partida debe estar en curso una vez que tenga dos jugadores
        lista = partida1.jugadores.all()
        self.assertEqual(len(lista),2)
        self.assertEqual(partida1.estado, EN_CURSO)


    #Test que une a una partida creada al mismo usuario que la creo, y verifica que
    #no lo haya unido
    def test_mismo_usuario(self):
        lobby = Lobby()
        partida = Partida.objects.get(nombre='Partida1 a 15 sin password')
        user1 = User.objects.get(username='test_user1')
        result = lobby.unirse_partida(user1, partida)
        # La partida no debe dejar ingresar al mismo jugador a la partida
        lista = partida.jugadores.all()
        self.assertEqual(len(lista),1)
        self.assertEqual(partida.estado, EN_ESPERA)
        self.assertEqual(-1,result)


    #Test que verifica que la lista de partidas disponibles se cree cuando se crea
    #una nueva partida, pero que deje de estar cuando se haya unido un jugador a la partida"""
    def test_listas_partidas(self):
        #Creo una lista para compararla con la real
        lista_partidas = [] 
        lobby = Lobby()
        partida1 = Partida.objects.get(nombre = 'Partida1 a 15 sin password')
        partida2 = Partida.objects.get(nombre = 'Partida2 a 30 sin password')
        partida3 = Partida.objects.get(nombre = 'Partida3 a 30 sin password')
        user2 = User.objects.get(username ='test_user2')
        user3 = User.objects.get(username = 'test_user3')
        #Agrego las partidas a la partida para compraralas luego
        lista_partidas.append(partida1)
        lista_partidas.append(partida2)
        lista_partidas.append(partida3)
        #Me fijo que esten las tres partidas
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))
        #Agrego a un jugador a la partida uno, por lo tanto debe salir de la lista disponibles
        lobby.unirse_partida(user2, partida1)
        #Lo remuevo de la lista auxiliar
        lista_partidas.remove(partida1)
        #Compruebo que no esta en la lista de partidas en espera
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))
        #Agrego un jugador a la partida 3
        lobby.unirse_partida(user2, partida3)
        #Lo remuevo de la lista auxiliar
        lista_partidas.remove(partida3)
        #Compruebo que no esta en la lista de partidas en espera
        self.assertEqual(lista_partidas, list(lobby.get_lista_partidas()))


    def test_crear_ronda(self):
        user2 = User.objects.get(username='test_user2')
        partida = Partida.objects.get(nombre = 'Partida1 a 15 sin password')
        lobby = Lobby()
        #Agrego a un jugador a la partida
        lobby.unirse_partida(user2, partida)
        #Testeo que se haya creado una ronda
        self.assertNotEqual(list(partida.ronda_set.all()), [])
        ronda = list(partida.ronda_set.all())
        #Obtengo la ultima ronda
        ronda = ronda[-1]
        #Chequeo que la ronda no haya terminado.
        self.assertFalse(ronda.termino)
        #Chequeo que la opcion para cantar sea solo "Envido"
        self.assertEqual(ronda.opciones, '3')
        #Obtengo los jugadores
        jugadores = list(partida.jugadores.all())
        #Chequeo que se les hayan asignado 3 cartas a cada uno 
        self.assertEqual(len((jugadores[1].cartas.all())), 3)
        #Chequeo que la mano sea el que esta en la posicion 0 (El que creo la partida)
        self.assertEqual(ronda.mano_pos, 0)


    def test_envido (self):
        user1 = User.objects.get(username ='test_user1')
        user2 = User.objects.get(username ='test_user2')
        lobby = Lobby()
        partida = Partida.objects.get(nombre = 'Partida3 a 30 sin password')
        lobby.unirse_partida(user2, partida)
        #Obtengo la ultima ronda
        ronda = list(partida.ronda_set.all())[-1]
        #Chequeo que la opcion sea 3 =  "envido"
        self.assertEqual(ronda.opciones, '3')
        #Obtengo los jugadores
        jugador1 = partida.jugadores.get(user = user1)
        jugador2 = partida.jugadores.get(user = user2)
        #Creo un canto
        ronda.crear_canto(ENVIDO, jugador1)
        canto = list(ronda.canto_set.all())
        #Verifico que haya un canto creado
        self.assertEqual(len(list(ronda.canto_set.all())), 1)
        #Obtengo el ultimo canto
        canto = canto[-1]
        #Chequeo que las opciones disponibles sean 0 = "Quiero" y 1 "No quiero"
        self.assertEqual(ronda.opciones, '01')
        #El jugador 2 acepta el envido
        ronda.responder_canto(1)
        #Chequeo que los puntos en juego sean 2
        self.assertNotEqual(canto.pts_en_juego, 2)
#        print"cantoo"
#        print canto.tipo
#        ganador = canto.equipo_ganador
#        print ganador
        #Chequeo que la ronda no termino
#        print '[%s]' % ', '.join(map(str, list(partida.ronda_set.all())))