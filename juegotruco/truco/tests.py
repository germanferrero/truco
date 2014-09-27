from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from truco.constants import *
from truco.models import *

class TrucoTests(TestCase):

    def test_estado_partidas(self):
        user1 = User.objects.create_user(username='test_user',
                                        email='email@email.com',
                                        password='asdf',)
        user2 = User.objects.create_user(username='test_user2',
                                        email='email2@email.com',
                                        password='asdf',)
        lobby = Lobby()
        partida = lobby.crear_partida(user=user1, nombre='Partida a 15 sin password',
                                      puntos_objetivo=15,password='')
        # La partida esta en espera hasta que se una un nuevo jugador
        self.assertEqual(partida.cantidad_jugadores,2)
        self.assertEqual(partida.estado, EN_ESPERA)
        lobby.unirse_partida(user2, partida)
        # La partida debe estar en curso una vez que tenga dos jugadores
        self.assertEqual(partida.cantidad_jugadores,2)
        self.assertEqual(partida.estado, EN_CURSO)
        # Falta estado de partidas

