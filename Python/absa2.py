import numpy as np
import pandas as pd

df_ratings = pd.read_csv('ml-latest-small/ml-latest-small/ratings.csv', usecols=['userId', 'movieId', 'rating'], dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})


# calculate adjusted ratings based on training data
rating_mean= df_ratings.groupby(['movieId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['movieId','rating_mean']]
adjusted_ratings = pd.merge(df_ratings,rating_mean,on = 'movieId', how = 'left', sort = False)
adjusted_ratings['rating_adjusted']=adjusted_ratings['rating']-adjusted_ratings['rating_mean']
# replace 0 adjusted rating values to 1*e-8 in order to avoid 0 denominator
adjusted_ratings.loc[adjusted_ratings['rating_adjusted'] == 0, 'rating_adjusted'] = 1e-8


# function of building the item-to-item weight matrix
def build_w_matrix(adjusted_ratings):
    # define weight matrix
    w_matrix_columns = ['movie_1', 'movie_2', 'weight']
    w_matrix=pd.DataFrame(columns=w_matrix_columns)

   # calculate the similarity values

    distinct_movies = np.unique(adjusted_ratings['movieId'])

    i = 0
    # for each movie_1 in all movies
    for movie_1 in distinct_movies:

        if i%10==0:
            print(i , "out of ", len(distinct_movies))

        # extract all users who rated movie_1
        user_data = adjusted_ratings[adjusted_ratings['movieId'] == movie_1]
        distinct_users = np.unique(user_data['userId'])

        # record the ratings for users who rated both movie_1 and movie_2
        record_row_columns = ['userId', 'movie_1', 'movie_2', 'rating_adjusted_1', 'rating_adjusted_2']
        record_movie_1_2 = pd.DataFrame(columns=record_row_columns)
        # for each customer C who rated movie_1
        for c_userid in distinct_users:
            print('build weight matrix for customer %d, movie_1 %d' % (c_userid, movie_1))
            # the customer's rating for movie_1
            c_movie_1_rating = user_data[user_data['userId'] == c_userid]['rating_adjusted'].iloc[0]
            # extract movies rated by the customer excluding movie_1
            c_user_data = adjusted_ratings[(adjusted_ratings['userId'] == c_userid) & (adjusted_ratings['movieId'] != movie_1)]
            c_distinct_movies = np.unique(c_user_data['movieId'])

            # for each movie rated by customer C as movie=2
            for movie_2 in c_distinct_movies:
                # the customer's rating for movie_2
                c_movie_2_rating = c_user_data[c_user_data['movieId'] == movie_2]['rating_adjusted'].iloc[0]
                record_row = pd.Series([c_userid, movie_1, movie_2, c_movie_1_rating, c_movie_2_rating], index=record_row_columns)
                record_movie_1_2 = record_movie_1_2.append(record_row, ignore_index=True)

        # calculate the similarity values between movie_1 and the above recorded movies
        distinct_movie_2 = np.unique(record_movie_1_2['movie_2'])
        # for each movie 2
        for movie_2 in distinct_movie_2:
            print('calculate weight movie_1 %d, movie_2 %d' % (movie_1, movie_2))
            paired_movie_1_2 = record_movie_1_2[record_movie_1_2['movie_2'] == movie_2]
            sim_value_numerator = (paired_movie_1_2['rating_adjusted_1'] * paired_movie_1_2['rating_adjusted_2']).sum()
            sim_value_denominator = np.sqrt(np.square(paired_movie_1_2['rating_adjusted_1']).sum()) * np.sqrt(np.square(paired_movie_1_2['rating_adjusted_2']).sum())
            sim_value_denominator = sim_value_denominator if sim_value_denominator != 0 else 1e-8
            sim_value = sim_value_numerator / sim_value_denominator
            w_matrix = w_matrix.append(pd.Series([movie_1, movie_2, sim_value], index=w_matrix_columns), ignore_index=True)

        i = i + 1

    return w_matrix


# calculate the predicted ratings
def predict(userId, movieId, w_matrix, adjusted_ratings, rating_mean):
   # fix missing mean rating which was caused by no ratings for the given movie
   # mean_rating exists for movieId
    if rating_mean[rating_mean['movieId'] == movieId].shape[0] > 0:
       mean_rating = rating_mean[rating_mean['movieId'] == movieId]['rating_mean'].iloc[0]
   # mean_rating does not exist for movieId(which may be caused by no ratings for the movie)
    else:
       mean_rating = 2.5

   # calculate the rating of the given movie by the given user
    user_other_ratings = adjusted_ratings[adjusted_ratings['userId'] == userId]
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