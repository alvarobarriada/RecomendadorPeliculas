import sqlite3
import pandas as pd
from fuzzywuzzy import fuzz
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import distance





#Variables globales
# Conexión con la base de datos SQLite
connection = sqlite3.connect(r'Database/Movielens.db')
cursor = connection.cursor()

cursor.execute('SELECT * FROM ratings')
result = cursor.fetchall()
ratings = pd.DataFrame.from_records(result, exclude = ['timestamp'], columns = ['userId' , 'movieId', 'rating', 'timestamp'])
df_movie_features = ratings.pivot( index= 'movieId', columns='userId', values='rating').fillna(0)

cursor.execute('SELECT * FROM movies')
result = cursor.fetchall()
movies = pd.DataFrame.from_records(result, exclude = ['genres'], columns = ['movieId' , 'title', 'genres'])
movie_to_idx = { movie: i for i, movie in enumerate(list(movies.set_index('movieId').loc[df_movie_features.index].title))}


#funcion que devuelve la matriz de pesos (ajustada item-item)
def matriz_ajustada(df_ratings):
    rating_mean= df_ratings.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]

    ratings = pd.merge(df_ratings,rating_mean,on = 'userId', how = 'left', sort = False)

    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']

    # replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
    ratings.loc[ratings['rating'] == 0, 'rating_adjusted'] = 1e-8
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

def cosine_similarity(adj,mov1,mov2):
    
    a = adj.loc[adj['movieId'] == mov1, 'rating_adjusted']
    b = adj.loc[adj['movieId'] == mov2, 'rating_adjusted']

    frame = { 'a': a, 'b': b }
    result = pd.DataFrame(frame).fillna(1e-8)

    scoreDistance = distance.cosine(result['a'], result['b'])

    #scoreDistance = spatial.distance.cosine(a, b)
    return scoreDistance

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

        if (subsetDataFrame2.empty):
            for valorada in valoradas:
                distancia = cosine_similarity(ajustada, movieId, valorada)
                #sin ajustar!
                rate_valorada = ratings.iloc[valorada]
                scoreB = rate_valorada['rating']
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


def recomendacion(userId):
    ajustada = matriz_ajustada(ratings)
    subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
    valoradas = subsetDataFrame1.get('movieId').tolist()
    array_ids_no_valoradas= []
    for i in range (0, 193610):
        if i not in valoradas:
            pelis = ajustada[ajustada['movieId'] == i]
            if (pelis.empty):
                pass
            else:
                print(i)
                array_ids_no_valoradas.append(i)
    for no_valorada in array_ids_no_valoradas:
        tupla_no_valorada = []
        for valorada in valoradas:
            similitud = cosine_similarity(ajustada, no_valorada, valorada)
            print(similitud)
            tupla_no_valorada.append((no_valorada, valorada, similitud))
        tupla_no_valorada = sorted(tupla_no_valorada, key=lambda x: x[2])[::-1]

    movieId = tupla_no_valorada[0][1]
    print(movieId)

recomendacion(2)