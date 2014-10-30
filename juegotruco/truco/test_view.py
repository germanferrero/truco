from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from truco.constants import *
from truco.models import *
from django.test import Client
from truco.views import *
from django.core.urlresolvers import reverse
from truco.forms import crear_partida_form


class TrucoViewTests(TestCase):
    def setUp(self):
        user1 = User.objects.create_user(username='test_user1', email='email@email.com',
                                         password='asdf',)
        user1.save()
        user2 = User.objects.create_user(username='test_user2', email='email@email.com',
                                         password='asdf',)
        user2.save()
        lobby = Lobby()
        partida1 = lobby.crear_partida(user=user1, nombre='Partida1',
                                       puntos_objetivo=15)
        partida1.save()
        response = self.client.post(
            reverse('usuarios:create_user'),
            {'username': 'test',
             'email': 'test@gmail.com',
             'password1': 'test',
             'password2': 'test',
             'first_name': 'test',
             'last_name': 'test'}
            )

    """
    Test que testea la vista de lobby
    """
    def test_lobby(self):
        #Hago un post
        response = self.client.post(reverse('truco:lobby'), {})
        #Debe devolver 200
        self.assertEqual(response.status_code, 200)
        # Debe redirigir al template lobby
        self.assertTemplateUsed(response, 'truco/lobby.html')

    """
    Test que testea la vista de index
    """
    def test_index(self):
        # Hago un get a index, por lo tanto el usuario esta logueado
        response = self.client.get(reverse('truco:index'))
        #Debe devolver 200
        self.assertEqual(response.status_code, 302)
        # Debe redireccionar a el lobby
        self.assertRedirects(response, reverse('truco:lobby'))

    """
    Test que testea la vista de crear_partida
    """
    def test_crear_partida(self):
        user2 = User.objects.get(username='test_user2')
        # Hago un get para que me muestre un formulario
        response = self.client.get(reverse('truco:crear_partida'), {})
        # Debe devolver 200
        self.assertEqual(response.status_code, 200)
        # Debe redirigir al template de crear partida para rellenar el formulario
        self.assertTemplateUsed(response, 'truco/crear_partida.html')
        # Testeo que el formulario que crea sea de la forma de crear_partida_form
        self.assertEqual(crear_partida_form, response.context['form'].__class__)
        response = self.client.post(reverse('truco:crear_partida'),
                                    {'user': user2,
                                     'nombre': 'nombre_partida',
                                     'puntos_objetivo': 15,})
        partida = Partida.objects.get(nombre='nombre_partida')
        # Redirige a partida
        self.assertRedirects(response, reverse('truco:partida', args=(partida.id,)))

    """
    Test que testea la vista de unirse_partida
    """
    def test_unirse_partida(self):
        user1 = User.objects.get(username='test_user1')
        partida1 = Partida.objects.get(nombre='Partida1')
        # Hago un get para que me muestre un formulario
        response = self.client.post(reverse('truco:unirse_partida'), {'partida': partida1.id})
        # Debe devolver 302
        self.assertEqual(response.status_code, 302)
        # Debe redireccionar a el en_espera
        self.assertRedirects(response, reverse('truco:en_espera', args=(partida1.id,)))


#    """
#    Test que testea la vista de partida (caso donde la partida ya esta terminada)
#    """
#    def partida_terminada(self):
#        user1 = User.objects.get (username = 'test_user1')
#        user2 = User.objects.get (username = 'test_user2')
#        partida = Partida.objects.get(nombre = 'Partida1')
#        ronda = partida.crear_ronda()

#        # Se asignan los puntajes a los jugadores, con uno de ellos como ganador
#        partida.puntos_e1 = 30
#        partida.puntos_e2 = 20
#        # Hago un get para que me muestre un formulario
#        response = self.client.post(reverse('truco:partida'),{'partida': partida.id})
#        # Debe devolver 302
#        self.assertEqual(response.status_code, 302)
#        # Debe redireccionar a el en_espera
#        self.assertRedirects(response, reverse('truco:en_espera', args=(partida1.id,)))
