import os
import connectorx as cx
import numpy as np
import implicit
from scipy.sparse import coo_matrix, save_npz

from django.contrib.auth.models import User
from movies.models import Rating, Movie

CONNECTION = f'postgres://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'

def run():
        """
        Generates a sparse user-item matrix from ratings dataframe. 
        IMPORTANT: Use this script only to generate a new matrix as
        it takes a lot of time to create it. If you're trying
        to extend the matrix with new rows (users) or columns (items)
        the util method csr_append() is used.
        """
        
        query = str(Rating.objects.all().values("owner_id", "movie_id", "value").query)
        df = cx.read_sql(CONNECTION, query)

        M = User.objects.count()
        N = Movie.objects.count()

        user_index = df['owner_id'] - 1
        item_index = df['movie_id'] - 1

        X = coo_matrix((df['value'], (user_index,item_index)), shape=(M,N), dtype=np.int8)
        X = X.tocsr()

        knn_model = implicit.nearest_neighbours.CosineRecommender()
        als_model = implicit.als.AlternatingLeastSquares(factors=50)

        knn_model.fit(X)
        als_model.fit(X)

        save_npz("data/X.npz", X)
        knn_model.save('data/knn_model')
        als_model.save('data/als_model')
        