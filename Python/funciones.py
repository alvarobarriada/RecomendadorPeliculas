#Librerias
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import requests
import sqlite3
from scipy.spatial.distance import cosine
from scipy.spatial import distance
#from sklearn.metrics.pairwise import cosine_similarity


#Variables globales
# Conexión con la base de datos SQLite
connection = sqlite3.connect(r'Database/Movielens.db')
cursor = connection.cursor()

cursor.execute('SELECT * FROM ratings')
result = cursor.fetchall()
ratings = pd.DataFrame.from_records(result, exclude = ['timestamp'], columns = ['userId' , 'movieId', 'rating', 'timestamp'])
df_movie_features = ratings.pivot( index= 'movieId', columns='userId', values='rating').fillna(np.NaN)

cursor.execute('SELECT * FROM movies')
result = cursor.fetchall()
movies = pd.DataFrame.from_records(result, exclude = ['genres'], columns = ['movieId' , 'title', 'genres'])
movie_to_idx = { movie: i for i, movie in enumerate(list(movies.set_index('movieId').loc[df_movie_features.index].title))}
connection.close()

# Función del coseno ajustado
"""
SIM(A,B) = sumatorio{ (ru,a - media(ru)) * (ru,b - media(ru)) } / sqrt{ sumatorio { [(ru,a - media(ru)]^2 } } * sqrt{ sumatorio { [(ru,b - media(ru)]^2 } }
Resultados entre [-1,1]
"""


#funcion que devuelve la matriz de pesos (ajustada item-item)
def matriz_ajustada(df_ratings):
    rating_mean= df_ratings.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]

    ratings = pd.merge(df_ratings,rating_mean,on = 'userId', how = 'left', sort = False)

    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']

    # replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
    ratings.loc[ratings['rating'] == np.NaN, 'rating_adjusted'] = np.NaN
    ratings = ratings.drop(['rating', 'rating_mean'], axis = 1)
    #ratings = ratings.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna()
    return ratings

#Esta función consigue que si el usuario comete una errata a la hora de introducir el titulo de la pelicula
#se encuentre igualmente
def fuzzy(movie_selected, verbose = True):
    try:
        match_tuple = []
        
        for title, idx in movie_to_idx.items():
            parecido = fuzz.ratio(title.lower(), movie_selected.lower())
            #Se mira si se parece y si es asi se guarda
            if parecido >= 65:
                connection = sqlite3.connect(r'Database/Movielens.db')
                cursor = connection.cursor()
                sql = 'SELECT * FROM movies where title = \'' + title + '\''
                cursor.execute(sql)
                result = cursor.fetchone()[0]
                connection.close()
                match_tuple.append((title, result, parecido))
            #Se ordena por ratio de parecido
            match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
        
        if not match_tuple:
            print('Pelicula no encontrada')
            return None

        return match_tuple
    except:
        return None

def cosine_similarity(adj,mov1,mov2):
    para_coseno = pd.concat([adj[mov1], adj[mov2]], axis=1, keys=[mov1, mov2])
    
    ajustada = para_coseno.dropna(how = 'any', axis = 'rows')
    if (ajustada.empty):
        scoreDistance = 0
    else:
        scoreDistance = cosine(ajustada[mov1], ajustada[mov2])
  
    return scoreDistance

def consultarBBDD(userId, movieId):
    connection = sqlite3.connect(r'Database/Movielens.db')
    cursor = connection.cursor()
    sql1 = 'SELECT rating FROM ratings where userId = '
    sql2= ' AND movieId = '
    sql = sql1 + str(userId) + sql2 + str(movieId)
    cursor.execute(sql)
    result = cursor.fetchone()
    connection.close()
    return result[0]

#funcion para la prediccion de la valoracion de una pelicula segun el usuario escogido
def prediccion(movieTitle, userId):
    pred = 0
    peli = fuzzy(movieTitle)
    if (peli != None):
        movieId = peli[0][1]
        ajustada = matriz_ajustada(ratings)
        
        subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
        valoradas = subsetDataFrame1.get('movieId').tolist()
        subsetDataFrame2 = subsetDataFrame1[subsetDataFrame1['movieId'] == movieId]
        sumatorioenumerador = 0
        sumatoriodenominador = 0
        ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)

        if (subsetDataFrame2.empty):
            for valorada in valoradas:
                distancia = cosine_similarity(ajustada, movieId, valorada)
                if (distancia != 0):
                    scoreB = consultarBBDD(userId, valorada)
                    numerador  = distancia * scoreB
                    sumatorioenumerador = sumatorioenumerador + numerador
                    sumatoriodenominador = sumatoriodenominador + distancia
            pred = sumatorioenumerador / sumatoriodenominador
            return pred
        else:
            pred = 1e-8
    else:
        pred = 1e-12
    return pred

def download_image(movieId):
    try:
        cursor = connection.cursor()
        sql = 'SELECT * FROM links where movieId = \'' + str(movieId) + '\''
        cursor.execute(sql)
        result = cursor.fetchone()[1]
        cursor.close()

        if (result != None):
            try:
                enlace = 'https://www.imdb.com/title/tt0' + str(result) + '/?ref_=nv_sr_srsg_0'
                page = requests.get(enlace)
                soup = BeautifulSoup(page.content, 'html.parser')
                div_poster = soup.find('div', class_ = "poster")
                imgimg = div_poster.find('img')
                imagen = imgimg['src']
                nombreArchivo = 'Database/img/'  + str(movieId) + '.jpg'
                with open(nombreArchivo, "wb") as f:
                    f.write(requests.get(imagen).content)
            except:
                print('Fallo en conexion')
    except:
        print('Fallo en la conexion a la BBDD')


def recomendacion():
    pass
