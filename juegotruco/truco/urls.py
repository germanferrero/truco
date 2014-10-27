from django.conf.urls import patterns, url

from truco import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^lobby$', views.lobby, name='lobby'),
    url(r'^crear_partida$', views.crear_partida, name='crear_partida'),
    url(r'^unirse_partida$', views.unirse_partida, name='unirse_partida'),
    url(r'^partida/(?P<partida_id>\d+)$', views.partida, name='partida'),
    url(r'^en_espera/(?P<partida_id>\d+)$', views.en_espera, name='en_espera'),
    url(r'^fin_de_ronda/(?P<partida_id>\d+)$', views.fin_de_ronda, name='fin_de_ronda'),
    url(r'^ronda/(?P<partida_id>\d+)$', views.ronda, name='ronda'),
    url(r'^tirar_carta/(?P<partida_id>\d+)/(?P<carta_id>\d+)$', views.tirar_carta, name='tirar_carta'),
    url(r'^responder_canto/(?P<partida_id>\d+)/(?P<opcion>\d+)$', views.responder_canto, name='responder_canto'),
)
