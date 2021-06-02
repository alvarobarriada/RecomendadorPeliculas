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
#Tabla ratings sin la columna de timestamp
cursor.execute('SELECT * FROM ratings')
result = cursor.fetchall()
ratings = pd.DataFrame.from_records(result, exclude = ['timestamp'], columns = ['userId' , 'movieId', 'rating', 'timestamp'])
df_movie_features = ratings.pivot( index= 'movieId', columns='userId', values='rating').fillna(np.NaN)
#Tabla movies sin la columna de genres
cursor.execute('SELECT * FROM movies')
result = cursor.fetchall()
movies = pd.DataFrame.from_records(result, exclude = ['genres'], columns = ['movieId' , 'title', 'genres'])
#Se usa para fuzzy
movie_to_idx = { movie: i for i, movie in enumerate(list(movies.set_index('movieId').loc[df_movie_features.index].title))}
#Cerramos conexion con la bbdd
connection.close()

#funcion que devuelve la matriz de pesos (ajustada)
def matriz_ajustada(df_ratings):
    #Columna con la media de cada usuario
    rating_mean= df_ratings.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]
    #Se junta con el resto de datos en base al userId
    ratings = pd.merge(df_ratings,rating_mean,on = 'userId', how = 'left', sort = False)
    #Generamos columna con el rating menos la media
    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']
    # Los valores no encontrados se guardan con un NaN
    ratings.loc[ratings['rating'] == np.NaN, 'rating_adjusted'] = np.NaN
    #Eliminamos las columnas de rating y de la media
    ratings = ratings.drop(['rating', 'rating_mean'], axis = 1)
    return ratings

#Esta función consigue que si el usuario comete una errata a la hora de introducir el titulo de la pelicula
#se encuentre igualmente
def fuzzy(movie_selected, verbose = True):
    try:
        match_tuple = []
        #Recorre todos los titulos de la bbdd
        for title, idx in movie_to_idx.items():
            #Busca el ratio de similitud entre el titulo de la bb y el que escribe el user
            parecido = fuzz.ratio(title.lower(), movie_selected.lower())
            #Si se parece mas de un 65%, fuimos probando para buscar un punto medio
            if parecido >= 65:
                #Se busca en la bbdd por el titulo que se ha encontrado
                connection = sqlite3.connect(r'Database/Movielens.db')
                cursor = connection.cursor()
                sql = 'SELECT * FROM movies where title = \'' + title + '\''
                cursor.execute(sql)
                result = cursor.fetchone()[0]
                connection.close()
                #Se guarda el titulo, el movieId y el ratio de similitud
                match_tuple.append((title, result, parecido))
            #Se ordena por ratio de similitud
            match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
        
        if not match_tuple:
            print('Pelicula no encontrada')
            return None
        #se devuelve el array de parecidos
        return match_tuple
    except:
        return None

def cosine_similarity(adj,mov1,mov2):
    scoreDistance = None
    #se genera un nuevo dataframe formado por las columnas de los movieId a comparar
    para_coseno = pd.concat([adj[mov1], adj[mov2]], axis=1, keys=[mov1, mov2])
    #se borran las filas que tengan al menos un NaN
    ajustada = para_coseno.dropna(how = 'any', axis = 'rows')
    #Si no queda nada despues de dropna se devuelve no
    if (ajustada.empty):
        pass
    else:
        #Se cambian los 0s por 1e-8 para evitar denominadores a 0
        ajustada.replace(0,1e-8)
        #Usando el coseno de la libreria spicy.spatial.distance
        scoreDistance = cosine(ajustada[mov1], ajustada[mov2])
    return scoreDistance

#Funcion que devuelve el rate de una movie de un usuario
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
    #Se busca los parecidos
    peli = fuzzy(movieTitle)
    if (peli != None):
        #Se accede al movie id del mas parecido
        movieId = peli[0][1]
        ajustada = matriz_ajustada(ratings)
        #En un nuevo dataframe se guardan las filas que tengan el userId que se esta analizando
        subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
        #Se guarda en un array los movieId que estan en el nuevo dataframe
        valoradas = subsetDataFrame1.get('movieId').tolist()
        #Se comprueba que la pelicula que se analiza no este ya valorada
        subsetDataFrame2 = subsetDataFrame1[subsetDataFrame1['movieId'] == movieId]
        #Variables para el calculo de la prediccion
        sumatorioenumerador = 0
        sumatoriodenominador = 0
        #Pivot nos sirve para generar una matriz como las de los apuntes, con las filas como userId
        #y las columnas con los movieId, y los elementos de esta las valoraciones ajustadas
        ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)
        #Si no esta valorada
        if (subsetDataFrame2.empty):
            #se recorren las valoradas
            for valorada in valoradas:
                #Calculamos la similitud
                distancia = cosine_similarity(ajustada, movieId, valorada)
                if (distancia != None):
                    #Obtenemos el rate del userId y la peli que toque
                    scoreB = consultarBBDD(userId, valorada)
                    numerador  = distancia * scoreB
                    #Realizamos los sumatorios
                    sumatorioenumerador = sumatorioenumerador + numerador
                    sumatoriodenominador = sumatoriodenominador + distancia
            #Comprobacion por si nunca encontro una similitud, para evitar divisiones entre 0
            if (sumatorioenumerador != 0 and sumatoriodenominador != 0):
                pred = sumatorioenumerador / sumatoriodenominador
            return pred
        #Si ya la ha valorado
        else:
            pred = 1e-8
    #si no se ha encontrado
    else:
        pred = 1e-12
    return pred

#Scrapper para la caratula de la pelicula
def download_image(movieId):
    try:
        #se obtiene el dato de imdb para la pelicula seleccionada 
        connection = sqlite3.connect(r'Database/Movielens.db')
        cursor = connection.cursor()
        sql = 'SELECT * FROM links where movieId = \'' + str(movieId) + '\''
        cursor.execute(sql)
        result = cursor.fetchone()[1]
        cursor.close()
        #Si se encuentra
        if (result != None):
            try:
                #tras analizar la forma de la pagina de imdb
                enlace = 'https://www.imdb.com/title/tt0' + str(result) + '/?ref_=nv_sr_srsg_0'
                #se descarga el contenido de la url
                page = requests.get(enlace)
                soup = BeautifulSoup(page.content, 'html.parser')
                #La caratula esta en un div con clase poster
                div_poster = soup.find('div', class_ = "poster")
                imgimg = div_poster.find('img')
                imagen = imgimg['src']
                #Se guarda con el nombre de su id
                nombreArchivo = 'Database/img/'  + str(movieId) + '.jpg'
                #Se descarga
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

def valoradas_bien (user,valoradas):
    media = 0
    valoradas_bien = []
    for va in valoradas:
        rate = consultarBBDD(user, va)
        media = media + rate
    media = media/len(valoradas)

    for val in valoradas:
        rat = consultarBBDD(user, val)
        if (rat >= media):
            valoradas_bien.append(val)
    
    return valoradas_bien


#Recomendacion, si no hay un valor, poner None
def predecir_recomendacion(userId, numero_ranking , umbral, vecinos):
    prediciones = []
    no_valoradas = no_valoradas_por(userId)
    no_valoradas.sort()
    #Para saber si ya encontro las predicciones 5.0 para la cantidad que busca
    contador = 0
    #Si especifica el umbral
    if (umbral != None):
        for no_valorada in no_valoradas:
            if contador < int(numero_ranking):
                ajustada = matriz_ajustada(ratings)
                subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
                valoradas = subsetDataFrame1.get('movieId').tolist()
                valorada_bien = valoradas_bien(userId, valoradas)
                sumatorioenumerador = 0
                sumatoriodenominador = 0
                ajustada = ajustada.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna(np.NaN)
                for valorada in valorada_bien:
                    distancia = cosine_similarity(ajustada, no_valorada, valorada)
                    if (distancia != None):
                        #Si la distancia es mayor o igual al umbral introducido
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
    #si especifica los vecinos      
    if(vecinos != None):
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
    print('--------RANKING----------')
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

predecir_recomendacion(1, 5 , 0.8, None)

