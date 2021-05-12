import numpy as np
import pandas as pd

df_ratings = pd.read_csv('ml-latest-small/ml-latest-small/ratings.csv', usecols=['userId', 'movieId', 'rating'], dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})


# calculate adjusted ratings based on training data
rating_mean= df_ratings.groupby(['movieId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['movieId','rating_mean']]
rankings = pd.merge(df_ratings,rating_mean,on = 'movieId', how = 'left', sort = False)
rankings['rating_adjusted']=rankings['rating']-rankings['rating_mean']
# replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
rankings.loc[rankings['rating_adjusted'] == 0, 'rating_adjusted'] = 1e-8


# function of building the item-to-item weight matrix
def build_w_matrix(rankings):
    # define weight matrix
    matriz_pesos_columnas = ['pelicula1', 'movie_2', 'peso']
    matriz_pesos=pd.DataFrame(columns=matriz_pesos_columnas)

   # calculate the similarity values

    peliculas = np.unique(rankings['movieId'])

    # for each pelicula1 in all movies
    for pelicula1 in peliculas:


        # extract all users who rated movie_1
        user_rating = rankings[rankings['movieId'] == pelicula1]
        usuarios = np.unique(user_rating['userId'])

        # record the ratings for users who rated both pelicula1 and movie_2
        columnas_a_guardar = ['userId', 'pelicula1', 'movie_2', 'rating_adjusted_1', 'rating_adjusted_2']
        record_movie_1_2 = pd.DataFrame(columns=columnas_a_guardar)
        # for each customer C who rated movie_1
        for user in usuarios:
            print('build weight matrix for customer %d, pelicula1 %d' % (user, pelicula1))
            # the customer's rating for pelicula1
            c_movie_1_rating = user_rating[user_rating['userId'] == user]['rating_adjusted'].iloc[0]
            # extract movies rated by the customer excluding pelicula1
            c_user_data = rankings[(rankings['userId'] == user) & (rankings['movieId'] != pelicula1)]
            c_distinct_movies = np.unique(c_user_data['movieId'])

            # for each movie rated by customer C as movie=2
            for movie_2 in c_distinct_movies:
                # the customer's rating for movie_2
                c_movie_2_rating = c_user_data[c_user_data['movieId'] == movie_2]['rating_adjusted'].iloc[0]
                record_row = pd.Series([user, pelicula1, movie_2, c_movie_1_rating, c_movie_2_rating], index=columnas_a_guardar)
                record_movie_1_2 = record_movie_1_2.append(record_row, ignore_index=True)

        # calculate the similarity values between pelicula1 and the above recorded movies
        distinct_movie_2 = np.unique(record_movie_1_2['movie_2'])
        # for each movie 2
        for movie_2 in distinct_movie_2:
            print('calculate weight movie_1 %d, movie_2 %d' % (pelicula1, movie_2))
            paired_movie_1_2 = record_movie_1_2[record_movie_1_2['movie_2'] == movie_2]
            sim_value_numerator = (paired_movie_1_2['rating_adjusted_1'] * paired_movie_1_2['rating_adjusted_2']).sum()
            sim_value_denominator = np.sqrt(np.square(paired_movie_1_2['rating_adjusted_1']).sum()) * np.sqrt(np.square(paired_movie_1_2['rating_adjusted_2']).sum())
            sim_value_denominator = sim_value_denominator if sim_value_denominator != 0 else 1e-8
            sim_value = sim_value_numerator / sim_value_denominator
            matriz_pesos = matriz_pesos.append(pd.Series([pelicula1, movie_2, sim_value], index=matriz_pesos_columnas), ignore_index=True)



    return matriz_pesos


# calculate the predicted ratings
def predict(userId, movieId, w_matrix, rankings, rating_mean):
   # fix missing mean rating which was caused by no ratings for the given movie
   # mean_rating exists for movieId
    if rating_mean[rating_mean['movieId'] == movieId].shape[0] > 0:
       mean_rating = rating_mean[rating_mean['movieId'] == movieId]['rating_mean'].iloc[0]
   # mean_rating does not exist for movieId(which may be caused by no ratings for the movie)
    else:
       mean_rating = 2.5

   # calculate the rating of the given movie by the given user
    user_other_ratings = rankings[rankings['userId'] == userId]
    user_distinct_movies = np.unique(user_other_ratings['movieId'])
    sum_weighted_other_ratings = 0
    sum_weghts = 0
    for movie_j in user_distinct_movies:
        if rating_mean[rating_mean['movieId'] == movie_j].shape[0] > 0:
           rating_mean_j = rating_mean[rating_mean['movieId'] == movie_j]['rating_mean'].iloc[0]
        else:
           rating_mean_j = 2.5
       # only calculate the weighted values when the weight between movie_1 and movie_2 exists in weight matrix
        w_movie_1_2 = w_matrix[(w_matrix['movie_1'] == movieId) & (w_matrix['movie_2'] == movie_j)]
        if w_movie_1_2.shape[0] > 0:
           user_rating_j = user_other_ratings[user_other_ratings['movieId']==movie_j]
           sum_weighted_other_ratings += (user_rating_j['rating'].iloc[0] - rating_mean_j) * w_movie_1_2['weight'].iloc[0]
           sum_weghts += np.abs(w_movie_1_2['weight'].iloc[0])

   # if sum_weights is 0 (which may be because of no ratings from new users), use the mean ratings
    if sum_weghts == 0:
        predicted_rating = mean_rating
   # sum_weights is bigger than 0
    else:
        predicted_rating = mean_rating + sum_weighted_other_ratings/sum_weghts

    return predicted_rating
