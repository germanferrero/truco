from django.test import TestCase
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.test import Client
from django.core.urlresolvers import reverse

class TrucoViewTests(TestCase):
    def setUp(self):
        response = self.client.post(reverse('usuarios:create_user'), 
                                {'username':'test',
                                'email': 'test@gmail.com',
                                'password1': 'test',
                                'password2': 'test',
                                'first_name': 'test',
                                'last_name':'test'})
        user1 = User.objects.create_user(username='test_user1', email='email@email.com',
                                        password='asdf',)
        user1.save()


    def test_create_user(self):
        # Creo un nuevo usuario
        response = self.client.post(reverse('usuarios:create_user'), 
                                {'username':'karen',
                                'email': 'karenhaag91@gmail.com',
                                'password1': 'karen',
                                'password2': 'karen',
                                'first_name': 'Karen',
                                'last_name':'Haag'})
        # Debe devolver error 302, dado que va a redireccionar la pagina
        self.assertEqual(response.status_code, 302)
        # Debe redireccionar a el lobby
        self.assertRedirects(response, reverse('truco:lobby'))
        # Creo otro usuario, pero esta vez sin completar todos los datos.
        response = self.client.post(reverse('usuarios:create_user'),
                                {'username':'karen',
                                'email': 'karenhaag91@gmail.com',
                                'password1': 'karen',
                                'first_name': 'Karen',
                                'last_name':'Haag'})
        #Debe devolver 200
        self.assertEqual(response.status_code, 200)
        # Debe redirigir al template crate_user
        self.assertTemplateUsed(response,'usuarios/create_user.html')



    def test_login (self):
        # Logueo un usuario que esta registrado
        response = self.client.post(reverse('usuarios:login'),
                                    {'username': 'test_user1',
                                     'password': 'asdf'})
        # Debe delvolver 302 para redirigir
        self.assertEqual(response.status_code, 302)
        # Debe redirigir al lobby
        self.assertRedirects(response, reverse('truco:lobby'))
        # Intento logear a un usuario que no existe
        response = self.client.post(reverse('usuarios:login'),
                                    {'username': 'otro_usuario',
                                     'password': 'asdf'})
        # Debe devolver 200 para redirigir al template
        self.assertEqual(response.status_code, 200)
        # Como los datos son incorrectos, debe redirigir al login nuevamente
        self.assertTemplateUsed(response,'usuarios/login.html')


    def test_logout (self):
        # Logueo un usuario que esta registrado
        response = self.client.post(reverse('usuarios:login'),
                                    {'username': 'test_user1',
                                     'password': 'asdf'})
        # Lo deslogueo
        response = self.client.post(reverse('usuarios:logout'),
                                    {'username': 'test_user1',
                                     'password': 'asdf'})
        # Debe delvolver 302 para redirigir
        self.assertEqual(response.status_code, 302)
# Falta ver el redirect....