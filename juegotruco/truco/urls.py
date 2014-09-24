from django.conf.urls import patterns, url

from truco import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^lobby$', views.lobby, name='lobby'),
    url(r'^crear_partida$', views.crear_partida, name='crear_partida'),
    url(r'^unirse_partida$', views.unirse_partida, name='unirse_partida'),
    url(r'^partida/(?P<partida_id>\d+)$', views.partida, name='partida'),
)
