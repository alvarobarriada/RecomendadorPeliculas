#Librerias
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import sqlite3
from scipy import spatial
from sklearn.metrics.pairwise import cosine_similarity

#Variables globales
# Conexión con la base de datos SQLite
connection = sqlite3.connect(r'/Users/sofiamartinezparada/Documents/GitHub/RecomendadorPeliculas/Database/Movielens.db')
cursor = connection.cursor()

cursor.execute('SELECT * FROM ratings')
result = cursor.fetchall()
ratings = pd.DataFrame.from_records(result, exclude = ['timestamp'], columns = ['userId' , 'movieId', 'rating', 'timestamp'])

df_movie_features = ratings.pivot( index= 'movieId', columns='userId', values='rating').fillna(0)

cursor.execute('SELECT * FROM movies')
result = cursor.fetchall()
movies = pd.DataFrame.from_records(result, exclude = ['genres'], columns = ['movieId' , 'title', 'genres'])
movie_to_idx = { movie: i for i, movie in enumerate(list(movies.set_index('movieId').loc[df_movie_features.index].title))}

# Función del coseno ajustado
"""
SIM(A,B) = sumatorio{ (ru,a - media(ru)) * (ru,b - media(ru)) } / sqrt{ sumatorio { [(ru,a - media(ru)]^2 } } * sqrt{ sumatorio { [(ru,b - media(ru)]^2 } }
Resultados entre [-1,1]
"""

# TODO: mezclar absa y absa2 para conseguir el código final


#funcion que devuelve la matriz de pesos (ajustada item-item)
def matriz_ajustada(df_ratings):
    rating_mean= df_ratings.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]

    ratings = pd.merge(df_ratings,rating_mean,on = 'userId', how = 'left', sort = False)

    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']

    # replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
    ratings.loc[ratings['rating'] == 0, 'rating_adjusted'] = 1e-8

    return ratings

#Esta función consigue que si el usuario comete una errata a la hora de introducir el titulo de la pelicula
#se encuentre igualmente
def fuzzy(matrix, movie_selected, verbose = True):
    match_tuple = []
    
    for title, idx in matrix.items():
        parecido = fuzz.ratio(title.lower(), movie_selected.lower())
        #Se mira si se parece y si es asi se guarda
        if parecido >= 65:
            cursor = connection.cursor()
            sql = 'SELECT * FROM movies where title = \'' + title + '\''
            cursor.execute(sql)
            result = cursor.fetchone()[0]
            match_tuple.append((title, result, parecido))
        #Se ordena por ratio de parecido
        match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
    
    if not match_tuple:
        print('Pelicula no encontrada')
        return

    if verbose:
        print('Se encontraron posibles parecidos en la bbdd: {0}\n'.format([x[0] for x in match_tuple]))
    return match_tuple
    #return match_tuple[0][1]

def cosine_similarity(ratings,mov1,mov2):
    a = ratings.iloc[mov1]
    b = ratings.iloc[mov2]

    scoreA = a['rating_adjusted']
    scoreB = b['rating_adjusted']
    scoreDistance = spatial.distance.cosine(a, b)
    return scoreDistance

#funcion para la prediccion de la valoracion de una pelicula segun el usuario escogido
def prediccion(movieTitle, userId, rating):
    pred = 0
    peli = fuzzy(movie_to_idx, movieTitle)
    movieId = peli[0][1]
    ajustada = matriz_ajustada(rating)
    subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
    valoradas = subsetDataFrame1.get('movieId').tolist()
    subsetDataFrame2 = subsetDataFrame1[subsetDataFrame1['movieId'] == movieId]
    sumatorioenumerador = 0
    sumatoriodenominador = 0

    if (subsetDataFrame2.empty):
        for valorada in valoradas:
            distancia = cosine_similarity(ajustada, movieId, valorada)
            #sin ajustar!
            rate_valorada = rating.iloc[valorada]
            scoreB = rate_valorada['rating']
            numerador  = distancia * scoreB
            sumatorioenumerador = sumatorioenumerador + numerador
            sumatoriodenominador = sumatoriodenominador + distancia

        pred = sumatorioenumerador / sumatoriodenominador
        return pred
    else:
        pred = 1e-8
    return pred


pred = prediccion('jumanji', 1, ratings)
print(pred)

#peli = fuzzy(movie_to_idx,'toy estory')

#Para acceder al nombre peli[0][0]
#Para el movieId peli[0][1]
#print(peli[0][0])
#print(peli[0][1])