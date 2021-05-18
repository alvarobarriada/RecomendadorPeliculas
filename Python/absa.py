import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix
import seaborn as sns
from sklearn.neighbors import NearestNeighbors

# Lectura de datos
df_movies = pd.read_csv('Database/ml-latest-small/ml-latest-small/movies.csv', usecols=['movieId', 'title'], dtype={'movieId': 'int32', 'title': 'str'})
df_ratings = pd.read_csv('Database/ml-latest-small/ml-latest-small/ratings.csv', usecols=['userId', 'movieId', 'rating'], dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})

# pivot ratings into movie features
df_movie_features = df_ratings.pivot( index= 'movieId', columns='userId', values='rating').fillna(0)
print(df_movie_features)


# create mapper from movie title to index
movie_to_idx = { movie: i for i, movie in enumerate(list(df_movies.set_index('movieId').loc[df_movie_features.index].title))}
#print(movie_to_idx)

# convert dataframe of movie features to scipy sparse matrix
mat_movie_features = csr_matrix(df_movie_features.values)
print(mat_movie_features)


model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=5)

model_knn.fit(mat_movie_features)


def fuzzy_matching(mapper, fav_movie, verbose=True):
    '''return the closest match via fuzzy ratio. If no match found, return None
 
        Parameters
        — — — — — 
        mapper: dict, map movie title name to index of the movie in data
        fav_movie: str, name of user input movie
        
        verbose: bool, print log if True
        Return
        — — — 
        index of the closest match'''
    match_tuple = []
    # get match
    for title, idx in mapper.items():
        ratio = fuzz.ratio(title.lower(), fav_movie.lower())
        if ratio >= 60:
            match_tuple.append((title, idx, ratio))
            # sort
            match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
    if not match_tuple:
        print('Oops! No match is found')
        return
    if verbose:
        print('Found possible matches in our database: {0}\n'.format([x[0] for x in match_tuple]))
        return match_tuple[0][1]

def make_recommendation(model_knn, data, mapper, fav_movie, n_recommendations):
    '''
    return top n similar movie recommendations based on user’s input movie
    Parameters
    — — — — — 
    model_knn: sklearn model, knn model
    data: movie-user matrix
    mapper: dict, map movie title name to index of the movie in data
    fav_movie: str, name of user input movie
    n_recommendations: int, top n recommendations
    Return
    — — — 
    list of top n similar movie recommendations
    '''
    # fit
    #model_knn.fit(data)
    # get input movie index
    print('You have input movie:', fav_movie)
    idx = fuzzy_matching(mapper, fav_movie, verbose=True)
    # inference
    print('Recommendation system start to make inference')
    print('……\n')
    distances, indices = model_knn.kneighbors(data[idx], n_neighbors=n_recommendations+1)
    # get list of raw idx of recommendations
    raw_recommends = \
    sorted(list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())), key=lambda x: x[1])[:0:-1]
    # get reverse mapper
    reverse_mapper = {v: k for k, v in mapper.items()}
    # print recommendations
    print('Recommendations for {}:'.format(fav_movie))
    for i, (idx, dist) in enumerate(raw_recommends):
        print('{0}: {1}, with distance of {2}'.format(i+1, reverse_mapper[idx], dist))


my_favorite = 'Pulp Fiction (1994)'
make_recommendation(model_knn=model_knn, data=mat_movie_features, fav_movie=my_favorite, mapper=movie_to_idx, n_recommendations=5)