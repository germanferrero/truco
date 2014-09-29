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
        user2 = User.objects.create_user(username='test_user2',email='email2@email.com',
                                        password='asdf',)
        user3 = User.objects.create_user(username='test_user3',email='email3@email.com',
                                        password='asdf',)
        lobby = Lobby()
        #Creo partidas
        partida1 = lobby.crear_partida(user=user1, nombre = 'Partida1 a 15 sin password',
                                    puntos_objetivo=15,password='')
        partida2 = lobby.crear_partida(user=user1, nombre = 'Partida2 a 30 sin password',
                                    puntos_objetivo=15,password='')
        partida3 = lobby.crear_partida(user=user1, nombre = 'Partida3 a 30 sin password',
                                    puntos_objetivo=15,password='')
        partida4 = lobby.crear_partida(user=user1, nombre = 'Partida4 con ambos jugadores',
                                    puntos_objetivo=15,password='')
        lobby.unirse_partida(user2, partida4)

#Creo maso de cartas, (ver si se puede mejorar)
        valor_espada = 1
        valor_bastos = 2
        valor_espada2 = 3
        valor_oro = 4
        valor_otro =7
        for i in range (1,5):
            palo_carta = i
            if palo_carta == 1:
                nombre_palo = "espadas"
            elif palo_carta == 2:
                nombre_palo = "bastos"
            elif palo_carta == 3:
                nombre_palo = "oro"
            elif palo_carta == 4:
                nombre_palo = "copas"
            for j in range (1,13):
                if j!=8 and j!=9:
                    nombre_carta = str(j)+" "+ 'de' +" "+ nombre_palo
                    if j==10 or j==11 or j==12:
                        envido = 0
                    else:
                        envido = j
                    if nombre_carta == "1 de espadas":
                        valor_jer = valor_espada
                    elif nombre_carta == '1 de bastos':

                        valor_jer = valor_bastos
                    elif nombre_carta == '7 de espadas':
                        valor_jer = valor_espada2
                    elif nombre_carta == '7 de oro':
                        valor_jer = valor_oro
                    else :
                        valor_jer = valor_otro
                    carta = Carta.objects.create(nombre = nombre_carta, valor_jerarquico = valor_jer,
                                            valor_envido = envido, palo = palo_carta, imagen = nombre_carta)
                    carta.save()
                    valor_otro = valor_otro-1
                    if valor_otro == 4:
                        valor_otro = 14



    #Test que se fija que una partida creada tiene seteado el estado en "EN_ESPERA".
    #Luego agrega un jugador nuevo a la partida y testea que se cambie el estado a "EN_CURSO"'''
    def test_estado_partidas(self):
        lobby = Lobby()
        partida1 = Partida.objects.get(nombre='Partida1 a 15 sin password')
        user2 = User.objects.get(username='test_user2')

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


    """Test que verifica que la lista de partidas disponibles se cree cuando se crea
    una nueva partida, pero que deje de estar cuando se haya unido un jugador a la partida"""
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
        lobby = Lobby()
        partida1 = Partida.objects.get(nombre = 'Partida4 con ambos jugadores')
        #Testeo que se haya creado una ronda
        self.assertNotEqual(list(partida1.ronda_set.all()), [])
        ronda = list(partida1.ronda_set.all())
        #Obtengo la ultima ronda
        ronda = ronda[-1]
        #Chequeo que la ronda no haya terminado.
        self.assertEqual(ronda.termino, False)
        #Chequeo que la opcion para cantar sea solo "Envido"
        self.assertEqual(ronda.opciones, str(3))







