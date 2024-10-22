import os
import orjson as json
import connectorx as cx
import numpy as np
import scipy.sparse as sp
import implicit

from django.contrib.auth.models import User
from movies import models

# Util methods to create, serialize and deserialize the X csr matrix.

def create_csr_and_models():
    query = str(models.Rating.objects.all().values("owner_id", "movie_id", "value").query)
    connection = f'postgres://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
    df = cx.read_sql(connection, query)

    M = User.objects.count()
    N = models.Movie.objects.count()

    user_index = df['owner_id'] - 1
    item_index = df['movie_id'] - 1

    X = sp.coo_matrix((df['value'], (user_index,item_index)), shape=(M,N), dtype=np.float32)
    X = X.tocsr()

    knn_model = implicit.nearest_neighbours.CosineRecommender()
    als_model = implicit.als.AlternatingLeastSquares(factors=50)

    knn_model.fit(X)
    als_model.fit(X)

    return X, knn_model, als_model

def jsonify(X):
    json_X = json.dumps(
        {
            "data": X.data, 
            "indices": X.indices, 
            "indptr": X.indptr,
            "shape": X.shape,
        }
    )
    return json_X

def json_to_csr(json_str):
    obj = json.loads(json_str)
    return sp.csr_matrix(
        (obj.get("data"), obj.get("indices"), obj.get("indptr")),
        shape=obj.get("shape")
    )