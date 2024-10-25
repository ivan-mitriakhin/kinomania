import os
import connectorx as cx
import numpy as np
import scipy.sparse as sp
import implicit

from django.contrib.auth.models import User
from movies import models

def create_csr_and_models():
    query = str(models.Rating.objects.all().values("owner_id", "movie_id", "value").query)
    connection = f'postgres://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_NAME")}'
    df = cx.read_sql(connection, query)

    M = User.objects.count()
    N = models.Movie.objects.count()

    user_index = df['owner_id'] - 1
    item_index = df['movie_id'] - 1

    X = sp.csr_matrix((df['value'], (user_index,item_index)), shape=(M,N), dtype=np.float32)

    knn_model = implicit.nearest_neighbours.CosineRecommender(K=15)
    als_model = implicit.cpu.als.AlternatingLeastSquares(factors=100)

    knn_model.fit(X)
    als_model.fit(X)

    return X, knn_model, als_model