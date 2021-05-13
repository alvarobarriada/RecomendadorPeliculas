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
def matriz_ajustada(df_ratings):
    rating_mean= df_ratings.groupby(['movieId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['movieId','rating_mean']]

    ratings = pd.merge(df_ratings,rating_mean,on = 'movieId', how = 'left', sort = False)

    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']

    # replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
    ratings.loc[ratings['rating_adjusted'] == 0, 'rating_adjusted'] = 1e-8
    
    return df_ratings

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
