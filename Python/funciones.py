#Librerias
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import numpy as np
import pandas as pd
import requests
from scipy.spatial.distance import cosine
import sqlite3


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
    scoreDistance = None
    para_coseno = pd.concat([adj[mov1], adj[mov2]], axis=1, keys=[mov1, mov2])
    
    ajustada = para_coseno.dropna(how = 'any', axis = 'rows')

    if (ajustada.empty):
        pass
    else:
        ajustada.replace(0,1e-8)
        scoreDistance = cosine(ajustada[mov1], ajustada[mov2])
    return scoreDistance

#Funcion que devuelve el rate
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

#Funcion que devuelve el titulo de una pelicula
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
        print(movieId)
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
                if (distancia != None):
                    scoreB = consultarBBDD(userId, valorada)
                    numerador  = distancia * scoreB
                    sumatorioenumerador = sumatorioenumerador + numerador
                    sumatoriodenominador = sumatoriodenominador + distancia
            if (sumatorioenumerador != 0 and sumatoriodenominador != 0):
                pred = sumatorioenumerador / sumatoriodenominador
                print(pred)
            return pred
        else:
            pred = 1e-8
    else:
        pred = 1e-12
    return pred

def download_image(movieId):
    try:
        connection = sqlite3.connect(r'Database/Movielens.db')
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

#Funcion que devuelve las peliculas valoradas por un user
def valoradas_por (userId):
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

def pelis_totales_valoradas():
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

#Funcion que devuelve las pelis no valoradas por un usuario
def no_valoradas_por (userId):
    user = valoradas_por(userId)
    valoradas = pelis_totales_valoradas()
    #Las pelis del total que no estan en las que valoro el user
    no_valoradas = np.setdiff1d(valoradas, user)
    return no_valoradas

#Recomendacion, si no hay un valor, poner None
def predecir_recomendacion(userId, numero_ranking , umbral, vecinos):
    prediciones = []
    no_valoradas = no_valoradas_por(userId)
    no_valoradas.sort()
    contador = 0
    if (numero_ranking  == None):
        numero_ranking = 5
    if (umbral != None):
        for no_valorada in no_valoradas:
            if contador < int(numero_ranking):
                ajustada = matriz_ajustada(ratings)
                subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
                valoradas = subsetDataFrame1.get('movieId').tolist()
                sumatorioenumerador = 0
                sumatoriodenominador = 0
                ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)
                for valorada in valoradas:
                    distancia = cosine_similarity(ajustada, no_valorada, valorada)
                    if (distancia != None):
                        if (distancia >= umbral):
                            scoreB = consultarBBDD(userId, valorada)
                            numerador  = distancia * scoreB
                            sumatorioenumerador = sumatorioenumerador + numerador
                            sumatoriodenominador = sumatoriodenominador + distancia
                if (sumatorioenumerador != 0 and sumatoriodenominador != 0):
                    pred = sumatorioenumerador / sumatoriodenominador
                    print('Id no valorada: ' , no_valorada)
                    print('Prediccion: ' , pred)
                    prediciones.append((no_valorada, pred))
                    if(pred == 5.0):
                        contador += 1
            
    if(vecinos != None):
        print(vecinos)
        for no_valorada in no_valoradas:
            if contador < int(numero_ranking):
                ajustada = matriz_ajustada(ratings)
                subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
                valoradas = subsetDataFrame1.get('movieId').tolist()
                sumatorioenumerador = 0
                sumatoriodenominador = 0
                ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)
                finales_vecinos =[]
                for valorada in valoradas:
                    distancia = cosine_similarity(ajustada, no_valorada, valorada)
                    if (distancia != None):
                        finales_vecinos.append((valorada, distancia))
                finales_vecinos.sort(reverse = True, key= lambda x: x[1])
                finales_vecino  = []
                if (vecinos < len(finales_vecinos)):
                    for i in (0, vecinos):
                        finales_vecino.append(finales_vecinos[i])
                else:
                    finales_vecino = finales_vecinos
                for final_ in finales_vecino:
                    valorar = final_[0]
                    dista = final_[1]
                    scoreB = consultarBBDD(userId, valorar)
                    numerador  = dista * scoreB
                    sumatorioenumerador = sumatorioenumerador + numerador
                    sumatoriodenominador = sumatoriodenominador + dista
                if (sumatorioenumerador != 0 and sumatoriodenominador != 0):
                    pred = sumatorioenumerador / sumatoriodenominador
                    print('Id no valorada: ' , no_valorada)
                    print('Prediccion: ' , pred)
                    prediciones.append((no_valorada, pred))
                    if(pred == 5.0):
                        contador += 1
    print('LLEGUE')
    final = []
    prediciones.sort(reverse = True, key= lambda x: x[1])
    if (int(numero_ranking) < (len(prediciones)-1)):
        for i in range (0, int(numero_ranking)):
            no_val = prediciones[i][0]
            predic = prediciones[i][1]
            titulo = consultarTitulo(no_val)
            print('Id no valorada: ' , no_val)
            print('Prediccion: ' , predic)
            final.append((titulo, predic))

    return final

#predecir_recomendacion(1,2,None, 1)

