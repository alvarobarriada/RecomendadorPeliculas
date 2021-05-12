#Librerias
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz

# Función del coseno ajustado
"""
SIM(A,B) = sumatorio{ (ru,a - media(ru)) * (ru,b - media(ru)) } / sqrt{ sumatorio { [(ru,a - media(ru)]^2 } } * sqrt{ sumatorio { [(ru,b - media(ru)]^2 } }
Resultados entre [-1,1]
"""
def cosenoAjustado(a, b):
    
    pass

# TODO: mezclar absa y absa2 para conseguir el código final


#funcion que devuelve la matriz de pesos (ajustada item-item)
def matriz_ajustada(rankings):
    #definimos la matriz de pesos
    matriz_pesos_columnas = ['pelicula1', 'pelicula2', 'peso']
    matriz_pesos = pd.DataFrame ( columns = matriz_pesos_columnas)

    #Calculamos la similitud de coseno

    #Guardamos en peliculas los valores de las peliculas sin repetir
    peliculas = np.unique(rankings['movieId'])

    for pelicula1 in peliculas:
        #guardamos los usuarios que hayan valorado la pelicula1
        user_rating = rankings[rankings['movieId'] == pelicula1]
        #Guardamos los valores de los users sin repetir
        usuarios = np.unique(user_rating['userId'])

        #Guardamos los ratings en un dataframe de usuarios que valoraros la pelicula1 y la pelicula2
        columnas_a_guardar = ['userId', 'pelicula1', 'pelicula2', 'ajustado1', 'ajustado2']
        pelicula1y2 = pd.DataFrame ( columns=columnas_a_guardar)

        #ahora recorremos los usuarios que han valorado la pelicula 1
        for user in usuarios:
            #Se guarda el valor de la valoracion del user de la pelicula1
            user_rating_pelicula1 = user_rating[user_rating['userId'] == user]['rating_ajustado'].iloc[0]

            #Se guardan las valoraciones del user de todas las peliculas menos de la pelicula 1
            user_rating_todas = rankings[(rankings['userId'] == user) & (rankings['movieId'] != pelicula1)]

            #Guardamos las peliculas distintas valoradas por el user
            pelis_distintas = np.unique(user_rating_todas['movieId'])

            #Recorremos las peliculas_distintas
            for pelicula2 in pelis_distintas:
                user_rating_pelicula2 = user_rating_todas[user_rating_todas['movieId'] == pelicula2]['rating_ajustado'].iloc(0)

                #Se genera una serie guardando la relacion entre pelicula 1 y pelicula 2
                actual = pd.Series([user, pelicula1, pelicula2, user_rating_pelicula1, user_rating_pelicula2], index = columnas_a_guardar)
                pelicula1y2 = pelicula1y2.append(actual, ignore_index=True)
        
        #Por ultimo, se calcula la similitud

        pelicula2_distinta = np.unique(pelicula1y2['pelicula2'])

        for pelicula2 in pelicula2_distinta:
            par = pelicula1y2[pelicula1y2['pelicula2']== pelicula2]
            
            enumerador = (par['ajustado1'] * par['ajustado2']).sum()
            denominador = np.sqrt(np.square(par['ajustado1']).sum() * np.sqrt(np.square(par['ajustado2'])).sum())
            denominador = denominador if denominador != 0 else 1e-15
            similitud = enumerador / denominador

            matriz_pesos = matriz_pesos.append(pd.Series([pelicula1, pelicula2, similitud], index= matriz_pesos_columnas ), ignore_index = True)
    
    return matriz_pesos

#Esta función consigue que si el usuario comete una errata a la hora de introducir el titulo de la pelicula
#se encuentre igualmente
def fuzzy(matrix, movie_selected, verbose = True):
    match_tuple = []
    
    for title, idx in matrix.items():
        parecido = fuzz.ratio(title.lower(), movie_selected.lower())
        #Se mira si se parece y si es asi se guarda
        if parecido >= 60:
            match_tuple.append(title, idx, parecido)
        #Se ordena por ratio de parecido
        match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
    
    if not match_tuple:
        print('Pelicula no encontrada')
        return

    if verbose:
        print('Se encontraron posibles parecidos en la bbdd: {0}\n'.format([x[0] for x in match_tuple]))
    
    return match_tuple[0][1]

#funcion para la prediccion de la valoracion de una pelicula segun el usuario escogido

def prediccion(userId, movieId, matriz_pesos, rankings, media):
    pass
