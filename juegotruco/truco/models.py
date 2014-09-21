from django.db import models


class Jugador(models.Model):
    nombre = models.CharField(max_length=32)


class Lobby(models.Model):

    def get_lista_partidas(self):
        lista_partidas = self.partida_set.all()
        return (lista_partidas)

    def crear_partida(self, jugador, puntos_objetivo, password):
        partida = Partida(
            lobby=self, puntos_objetivo=puntos_objetivo, password=password)
        partida.save(force_insert=True)
        partida.jugadores.add(jugador)
        partida.mano = jugador.id
        partida.save()
        return 0


class Partida(models.Model):
    lobby = models.ForeignKey(Lobby)
    jugadores = models.ManyToManyField(Jugador, verbose_name='jugadores')
    puntos_objetivo = models.IntegerField(default=15)
    password = models.CharField(max_length=16)
    estado = models.IntegerField(default=0)
    mano = models.IntegerField(default=0)
