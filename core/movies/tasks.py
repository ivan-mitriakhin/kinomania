from django.core.cache import cache

from celery import shared_task
from celery.signals import celeryd_init
from contextlib import contextmanager
import pickle
import time
import socket
import numpy as np

from utils import csr_utils

LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes

@contextmanager
def cache_lock(lock_id, oid):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)

@celeryd_init.connect(sender=f"worker1@{socket.gethostname()}")
def at_start(sender, **kwargs):
    X, knn_model, als_model = csr_utils.create_csr_and_models()
    pkl_X = pickle.dumps(X)
    pkl_knn = pickle.dumps(knn_model)
    pkl_als = pickle.dumps(als_model)
    cache.set('X', pkl_X, timeout=None)
    cache.set('knn_model', pkl_knn, timeout=None)
    cache.set('als_model', pkl_als, timeout=None)

@shared_task(bind=True)
def csr_append_task(self, axis):
    lock_id = 'csr_lock'

    with cache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            if axis not in [0, 1]:
                raise ValueError(f"No axis named { axis }, please choose between 0 and 1.")
            
            X = pickle.loads(cache.get('X'))
            
            if axis == 0:
                X._shape = (X.shape[0] + 1, X.shape[1])
                X.indptr = np.hstack((X.indptr,X.indptr[-1]))
            else:
                X._shape = (X.shape[0], X.shape[1] + 1)

            pkl_X = pickle.dumps(X)
            cache.set('X', pkl_X, timeout=None)
            return
        
    raise self.retry(countdown=10)

@shared_task(bind=True)
def csr_update_task(self, owner_pk, movie_pk, value, save):
    lock_id = 'csr_lock'

    with cache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            i = owner_pk - 1
            j = movie_pk - 1
            X = pickle.loads(cache.get('X'))
            knn_model = pickle.loads(cache.get('knn_model'))
            als_model = pickle.loads(cache.get('als_model'))

            if save:
                X[i, j] = value
            else:
                X[i, j] = 0
                X.eliminate_zeros()

            knn_model.fit(X, False)
            als_model.partial_fit_users([i], X[i])
            als_model.partial_fit_items([j], X.T[j])

            pkl_X = pickle.dumps(X)
            pkl_knn = pickle.dumps(knn_model)
            pkl_als = pickle.dumps(als_model)
            cache.set('X', pkl_X, timeout=None)
            cache.set('knn_model', pkl_knn, timeout=None)
            cache.set('als_model', pkl_als, timeout=None)
            return
    
    raise self.retry(countdown=10)

