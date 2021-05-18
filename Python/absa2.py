import numpy as np
import pandas as pd

df_ratings = pd.read_csv('ml-latest-small/ml-latest-small/ratings.csv', usecols=['userId', 'movieId', 'rating'], dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})


# calculate adjusted ratings based on training data
rating_mean= df_ratings.groupby(['movieId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['movieId','rating_mean']]
rankings = pd.merge(df_ratings,rating_mean,on = 'movieId', how = 'left', sort = False)
rankings['rating_adjusted']=rankings['rating']-rankings['rating_mean']
# replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
rankings.loc[rankings['rating_adjusted'] == 0, 'rating_adjusted'] = 1e-8



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
