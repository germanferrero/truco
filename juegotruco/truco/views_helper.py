from truco.models import Partida, Ronda, Carta
from truco.constants import *

def puntos_cantados_validos(puntos_cantados, ronda, jugador):
    result = False
    try:
        puntos = int(puntos_cantados)
        if 0 <= int(puntos) <= 33:
            ronda.ultimo_envido().cantar_puntos(jugador, puntos)
            result = True
    except:
        pass
    return result

def no_es_mas_mi_turno(partida, ronda, jugador, opcion):
    if opcion == IRSE_AL_MAZO:
        ronda.irse_al_mazo(jugador)
    elif opcion == SON_BUENAS:
        ronda.ultimo_envido().cantar_puntos(jugador, -2)
        # Se usa -2 para diferenciar con los casos: -1(no hay mensajes que
        # mostrar al jugador), 0 (tener 0 puntos)
    elif opcion in [ENVIDO, TRUCO, REAL_ENVIDO, FALTA_ENVIDO]:
        # Hay un canto inicial
        puntos_restantes = partida.get_min_pts_restantes()
        ronda.crear_canto(opcion, jugador, puntos_restantes)

