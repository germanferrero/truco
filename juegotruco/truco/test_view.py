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
        user1 = User.objects.create_user(username ='test_user1', email ='email@email.com',
                                        password ='asdf',)
        user1.save()
        user2 = User.objects.create_user(username ='test_user2', email ='email@email.com',
                                        password ='asdf',)
        user2.save()
        lobby = Lobby()
        partida1 = lobby.crear_partida(user = user1, nombre = 'Partida1 a 15 sin password',
                                    puntos_objetivo = 15,password ='')
        partida1.save()

        response = self.client.post(reverse('usuarios:create_user'), 
                                {'username':'test',
                                'email': 'test@gmail.com',
                                'password1': 'test',
                                'password2': 'test',
                                'first_name': 'test',
                                'last_name':'test'})

    def test_lobby(self):
        #Hago un post
        response = self.client.post (reverse('truco:lobby'),{})
        #Debe devolver 200
        self.assertEqual(response.status_code, 200)
        # Debe redirigir al template lobby
        self.assertTemplateUsed(response,'truco/lobby.html')


    def test_index (self):
        # Hago un get a index, por lo tanto el usuario esta logueado
        response = self.client.get(reverse('truco:index'), {})
        #Debe devolver 200
        self.assertEqual(response.status_code, 302)
        # Debe redireccionar a el lobby
        self.assertRedirects(response, reverse('truco:lobby'))
        # Falta hacer el post... ver como es....


    def test_crear_partida(self):
        user2 = User.objects.get (username = 'test_user2')
        # Hago un get para que me muestre un formulario
        response = self.client.get (reverse('truco:crear_partida'),{})
        # Debe devolver 200
        self.assertEqual(response.status_code, 200)
        # Debe redirigir al template de crear partida para rellenar el formulario
        self.assertTemplateUsed(response,'truco/crear_partida.html')
        # Testeo que el formilario que crea sea de la forma de crear_partida_form
        self.assertEqual(crear_partida_form, response.context['form'].__class__)