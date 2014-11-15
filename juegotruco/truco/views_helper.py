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
        pass  # result = False
    return result

def respuestas_a_cantos(ronda, opcion):
    return(opcion in [DOBLE_ENVIDO, REAL_ENVIDO, FALTA_ENVIDO]
                    and ronda.ultimo_envido()
                    or opcion in [RETRUCO, VALE_CUATRO]
                    or opcion in [QUIERO, NO_QUIERO])

def nuevo_canto(opcion):
    return opcion in [ENVIDO, TRUCO, REAL_ENVIDO, FALTA_ENVIDO]

def set_perdedor_envido(ronda, jugador):
    ronda.ultimo_envido().cantar_puntos(jugador, -2)
    # Se usa -2 para diferenciar con los casos: -1(no hay mensajes que
    # mostrar al jugador), 0 (tener 0 puntos)

def responder_canto_aux(partida, jugador, opcion):
    ronda = partida.get_ronda_actual()
    canto_actual = ronda.get_ultimo_canto()
    if int(opcion) == QUIERO:
        canto_actual.aceptar()
    elif int(opcion) == NO_QUIERO:
        canto_actual.rechazar()
    else:
        canto_actual.aumentar(int(opcion),jugador.posicion_mesa)