#Librerias
from aem import con
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import requests
import sqlite3
from scipy.spatial.distance import cosine



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
    ratings.loc[ratings['rating'] == np.NaN, 'rating_adjusted'] = np.NaN
    ratings = ratings.drop(['rating', 'rating_mean'], axis = 1)
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

                    cursor = connection.cursor()
                    sql = 'SELECT * FROM movies where title = \'' + title + '\''
                    cursor.execute(sql)
                    result = cursor.fetchone()[0]
                    match_tuple.append((title, result, parecido))
            #Se ordena por ratio de parecido
            match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
        
        if not match_tuple:
            print('Pelicula no encontrada')
            return None

        return match_tuple
    except:
        return None

def cosine_sim(df1, df2):
    
    df1na = df1.isna()
    df1clean = df1[~df1na]
    df2clean = df2[~df1na]

    df2na = df2clean.isna()
    df1clean = df1clean[~df2na]
    df2clean = df2clean[~df2na]


    # Compute cosine similarity
    distance = cosine(df1clean, df2clean)
    sim = 1 - distance

    return sim

'''
def id_pelis_total():
    array_pelis = []
    connection = sqlite3.connect(r'Database/Movielens.db')
    cursor = connection.cursor()

    cursor.execute('SELECT movieId FROM movies')
    result = cursor.fetchall()
    connection.close()

    for movie in result:
        array_pelis.append(movie[0])
    return array_pelis
'''

def id_pelis_user(userId):
    array_pelis = []
    connection = sqlite3.connect(r'Database/Movielens.db')
    cursor = connection.cursor()
    sql = 'SELECT movieId FROM ratings where userId = '
    consulta= sql + str(userId)
    cursor.execute(consulta)
    result = cursor.fetchall()
    connection.close()
    for movie in result:
        array_pelis.append(movie[0])
    return array_pelis

def id_pelis_valoradas():
    array_pelis = []
    connection = sqlite3.connect(r'Database/Movielens.db')
    cursor = connection.cursor()
    sql = 'SELECT movieId FROM ratings'
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()
    for movie in result:
        if movie[0] not in array_pelis:
            array_pelis.append(movie[0])
    return array_pelis


def pelis_no_valoradas(usuario):
    #totales = id_pelis_total()
    user = id_pelis_user(usuario)
    valoradas = id_pelis_valoradas()
    #no_valoradas = np.setdiff1d(totales , valoradas)
    #main_list = np.setdiff1d(no_valoradas , totales)
    main_list = np.setdiff1d(valoradas,user)
    return main_list


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

def consultarTitulo (movieId):
    connection = sqlite3.connect(r'Database/Movielens.db')
    cursor = connection.cursor()
    sql1 = 'SELECT title FROM movies where movieId = '
    sql = sql1 + str(movieId) 
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
        ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(1e-12)

        if (subsetDataFrame2.empty):
            for valorada in valoradas:
                distancia = cosine_sim(ajustada[movieId], ajustada[valorada])

                #distancia = cosine_similarity(ajustada, movieId, valorada)
                #sin ajustar!
                scoreB = consultarBBDD(userId, valorada)
                '''
                rate_valorada = ratings.iloc[valorada]
                scoreB = rate_valorada['rating']'''
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
    


#funcion para la prediccion de la valoracion de una pelicula segun el usuario escogido
def prediccion_rec(movieId, userId):
    pred = 0
    ajustada = matriz_ajustada(ratings)
    subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
    valoradas = subsetDataFrame1.get('movieId').tolist()
    sumatorioenumerador = 0
    sumatoriodenominador = 0
    ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(1e-8)
    for valorada in valoradas:
        distancia = cosine_sim(ajustada[movieId], ajustada[valorada])
        #distancia = cosine_similarity(ajustada, movieId, valorada)
        #sin ajustar!
        scoreB = consultarBBDD(userId, valorada)
        numerador  = distancia * scoreB
        sumatorioenumerador = sumatorioenumerador + numerador
        sumatoriodenominador = sumatoriodenominador + distancia

    pred = sumatorioenumerador / sumatoriodenominador
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




def rec (userId, umbral, numrank):
    global ratings
    array_valoradas_bien = []
    tupla_bien = []
    ajustada = matriz_ajustada(ratings)
    ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)
    ajustada = ajustada.dropna(how = 'all', axis = 'columns')

    valoradas = id_pelis_user(userId)
    rating_mean= ratings.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]
    ratings_mean = pd.merge(ratings,rating_mean,on = 'userId', how = 'left', sort = False)
    subsetDataFrame1 = ratings_mean[ratings_mean['userId'] == userId]
    mean = subsetDataFrame1.get('rating_mean').tolist()[0]
    
    for valorada in valoradas:
        rate = consultarBBDD(userId, valorada)
        if (rate >= mean):
            array_valoradas_bien.append(valorada)
    no_valoradas = pelis_no_valoradas(userId)

    for no_val in no_valoradas:
        for valor_bien in array_valoradas_bien:
            distansia = cosine_sim(ajustada[no_val], ajustada[valor_bien])
            if distansia >= umbral:
                rate = consultarBBDD(userId, valor_bien)
                tupla_bien.append((distansia, rate, no_val, valor_bien))
    if(len(tupla_bien)!= 0):
        tupla_bien.sort(reverse=True, key=lambda x: (x[0], -x[1]))

        print('Acabo la parte de similitud')
        predicciones = []
        for i in range (0, numrank):
            a_predecir = tupla_bien[i][2]
            title = consultarTitulo(a_predecir)
            pred = prediccion(title,userId)
            if (predicciones[len(predicciones)-1][1] != a_predecir):
                predicciones.append((pred, a_predecir))
            
        predicciones.sort(reverse=True, key=lambda x: x[0])
        for i in range (0, numrank):
            pred = predicciones[i][0]
            peli = predicciones[i][1]
            titulo = consultarTitulo(peli)
            print(pred)
            print(titulo)
            print('**************')
    else:
        print('No hay peliculas con ese umbral de similitud')



rec(30, 1.0, 5)

#print(prediccion('Balto (1995)', 30))