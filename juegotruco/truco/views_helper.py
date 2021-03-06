from truco.models import Partida, Ronda, Carta, Jugador
from truco.constants import *

def puntos_cantados_validos(puntos_cantados, ronda, jugador):
    result = False
    try:
        puntos = int(puntos_cantados)
        if (0 <= int(puntos)) and (int(puntos) <= 33):
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

"""
Extiende la lista de cantidad de cartas de los jugadores para usar en el template.
Es necesario obtener un iterable para cada uno de ellos
"""
def lista_cantidad_cartas(lista):
    list_cant_cartas = [0 for i in range(5)]
    cantidad_jugadores = len(lista) + 1
    if cantidad_jugadores == 2:
        list_cant_cartas[4] = lista[0]
    elif cantidad_jugadores == 4:
        list_cant_cartas[0] = lista[0]
        list_cant_cartas[3] = lista[1]
        list_cant_cartas[4] = lista[2]
    else:
        list_cant_cartas = lista
    list_cant_cartas = [[i+1 for i in range(j)] for j in list_cant_cartas]
    return list_cant_cartas


"""
Extiende la lista de cartas jugadas de cada jugador, comenzando por el jugador que lo utiliza
para usar en el template.
"""
def lista_cartas_jugadores(lista):
    list_cartas_jugadores = [[] for i in range(6)]
    cantidad_jugadores = len(lista)
    list_cartas_jugadores[0] = lista[0]
    if cantidad_jugadores == 2:
        list_cartas_jugadores[5] = lista[1]
    elif cantidad_jugadores == 4:
        list_cartas_jugadores[1] = lista[1]
        list_cartas_jugadores[4] = lista[2]
        list_cartas_jugadores[5] = lista[3]
    else:
        list_cartas_jugadores = lista
    return list_cartas_jugadores

"""
Extiende la lista de cartas jugadas de cada jugador, comenzando por el jugador que lo utiliza
para usar en el template.
"""
def lista_cartas_jugadores(lista):
    list_cartas_jugadores = [[] for i in range(6)]
    cantidad_jugadores = len(lista)
    list_cartas_jugadores[0] = lista[0]
    if cantidad_jugadores == 2:
        list_cartas_jugadores[5] = lista[1]
    elif cantidad_jugadores == 4:
        list_cartas_jugadores[1] = lista[1]
        list_cartas_jugadores[4] = lista[2]
        list_cartas_jugadores[5] = lista[3]
    else:
        list_cartas_jugadores = lista
    return list_cartas_jugadores

"""
Extiende la lista de nombres de jugadores para usar en el template.
"""
def lista_nombres_jugadores(lista):
    lista_nombres_jugadores = ['' for i in range(6)]
    cantidad_jugadores = len(lista)
    lista_nombres_jugadores[0] = lista[0]
    if cantidad_jugadores == 2:
        lista_nombres_jugadores[5] = lista[1]
    elif cantidad_jugadores == 4:
        lista_nombres_jugadores[1] = lista[1]
        lista_nombres_jugadores[4] = lista[2]
        lista_nombres_jugadores[5] = lista[3]
    else:
        lista_nombres_jugadores = lista
    return lista_nombres_jugadores



