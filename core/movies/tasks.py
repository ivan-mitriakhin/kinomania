from celery import shared_task
from celery.signals import worker_init
import pickle
import numpy as np

from movies.apps import MoviesConfig
from utils import csr_utils

r = MoviesConfig.redis_client
X, knn_model, als_model = None, None, None

@worker_init.connect
def at_start(sender, **kwargs):
    X, knn_model, als_model = csr_utils.create_csr_and_models()
    pkl_X = pickle.dumps(X)
    pkl_knn = pickle.dumps(knn_model)
    pkl_als = pickle.dumps(als_model)
    r.set('X', pkl_X)
    r.set('knn_model', pkl_knn)
    r.set('als_model', pkl_als)

@shared_task
def csr_append_task(axis=0):
    if axis not in [0, 1]:
        raise ValueError(f"No axis named { axis }, please choose between 0 and 1.")
    
    if axis == 0:
        X._shape = (X.shape[0] + 1, X.shape[1])
        X.indptr = np.hstack((X.indptr,X.indptr[-1]))
    else:
        X._shape = (X.shape[0], X.shape[1] + 1)

    pkl_X = pickle.dumps(X)
    r.set('X', pkl_X)

@shared_task()
def csr_update_task(owner_pk, movie_pk, value, save=True):
    i = owner_pk - 1
    j = movie_pk - 1

    if save:
        X[i, j] = value
    else:
        X[i, j] = 0
        X.eliminate_zeros()

    knn_model.fit(X, show_progress=False)
    als_model.partial_fit_users([i], X[i])
    als_model.partial_fit_items([j], X.T[j])

    pkl_X = pickle.dumps(X)
    pkl_knn = pickle.dumps(knn_model)
    pkl_als = pickle.dumps(als_model)
    r.set('X', pkl_X)
    r.set('knn_model', pkl_knn)
    r.set('als_model', pkl_als)

