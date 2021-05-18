from numpy import NaN
import pandas as pd
from scipy.spatial import distance
from surprise import KNNBasic
algo = KNNBasic()

dat = {'userId': ['vera', 'vera','vera','vera','vera','usuario1','usuario1','usuario1','usuario1','usuario1','usuario2','usuario2','usuario2','usuario2','usuario2','usuario3','usuario3','usuario3','usuario3','usuario3','usuario4','usuario4','usuario4','usuario4','usuario4'],
'movieId': ['e1', 'e2','e3','e4','e5','e1','e2','e3','e4','e5','e1','e2','e3','e4','e5','e1','e2','e3','e4','e5','e1','e2','e3','e4','e5'],
'rating' : [5., 3.,4.,4.,NaN,3.,1.,2.,3.,3.,4.,3.,4.,3.,5.,3.,3.,1.,5.,4.,1.,5.,5.,2.,1.]
}

df = pd.DataFrame(dat, columns = ['userId', 'movieId', 'rating'])

print (df)

def matriz_ajustada(df):
    rating_mean= df.groupby(['userId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['userId','rating_mean']]

    ratings = pd.merge(df,rating_mean,on = 'userId', how = 'left', sort = False)

    ratings['rating_adjusted']=ratings['rating']-ratings['rating_mean']

    # replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
    ratings.loc[ratings['rating'] == 0, 'rating_adjusted'] = 1e-8
    ratings = ratings.drop(['rating', 'rating_mean'], axis = 1)
    #ratings = ratings.pivot( index= 'userId', columns='movieId', values='rating_adjusted').fillna()
    return ratings

aj = matriz_ajustada(df)
print(aj)


def cosine_similarity(adj,mov1,mov2):
    a = adj.loc[adj['movieId'] == mov1, 'rating_adjusted']
    b = adj.loc[adj['movieId'] == mov2, 'rating_adjusted']
    frame = { 'a': a, 'b': b }
    result = pd.DataFrame(frame).fillna(1e-8)

    scoreDistance = distance.cosine(result['a'], result['b'])
    return scoreDistance


#funcion para la prediccion de la valoracion de una pelicula segun el usuario escogido
def prediccion(userId):
    pred = 0
    #peli = fuzzy(movieTitle)
    peli = 'e5'
    if (peli != None):
        movieId = 'e5'
        ajustada = matriz_ajustada(df)
        subsetDataFrame1 = ajustada[ajustada['userId'] == userId]
        #valoradas = subsetDataFrame1.get('movieId').tolist()
        valoradas = ['e1', 'e2', 'e3', 'e4']
        subsetDataFrame2 = subsetDataFrame1[subsetDataFrame1['movieId'] == movieId]
        sumatorioenumerador = 0
        sumatoriodenominador = 0

        for valorada in valoradas:
            distancia = cosine_similarity(ajustada, movieId, valorada)
            #sin ajustar!
            #scoreB = df.loc[df['movieId'] == valorada, df['userId'] == userId , 'rating']
            scoreB = df.loc[df['movieId'] == valorada]
            print(scoreB)
            numerador  = distancia * scoreB
            sumatorioenumerador = sumatorioenumerador + numerador
            sumatoriodenominador = sumatoriodenominador + distancia

        pred = sumatorioenumerador / sumatoriodenominador
        return pred
 
        
    else:
        pred = 1e-12
    
    return pred

prediccion('vera')

