import numpy as np
import scipy.sparse as sp
from zipfile import BadZipfile

def load_X():
    while True:
        try:
            X = sp.load_npz("data/X.npz")
        except (BadZipfile, EOFError):
            print("X is being saved into the system, please wait.")
        else:
            print("X loaded successfully.")
            break
    return X

def csr_append(X=None, axis=0):
        if axis not in [0, 1]:
            raise ValueError(f"No axis named { axis }, please choose between 0 and 1.")
        if not X:
            X = load_X()
        model = None
        
        if axis == 0:
            model = MyUser
            X._shape = (X.shape[0] + 1, X.shape[1])
            X.indptr = np.hstack((X.indptr,X.indptr[-1]))
        else:
            model = Movie
            X._shape = (X.shape[0], X.shape[1] + 1)

        idx = X.shape[axis] - 1
        pk = model.objects.count()
        if axis == 0:
            movie_mapper = np.load("data/movie_mapper.npy", allow_pickle=True).item()
            movie_inv_mapper = np.load("data/movie_inv_mapper.npy", allow_pickle=True).item()
            movie_mapper[pk] = idx
            movie_inv_mapper[idx] = pk
            np.save("data/movie_mapper.npy", movie_mapper)
            np.save("data/movie_inv_mapper.npy", movie_inv_mapper)
        else:
            user_mapper = np.load("data/user_mapper.npy", allow_pickle=True).item()
            user_inv_mapper = np.load("data/user_inv_mapper.npy", allow_pickle=True).item()
            user_mapper[pk] = idx
            user_inv_mapper[idx] = pk
            np.save("data/user_mapper.npy", user_mapper)
            np.save("data/user_inv_mapper.npy", user_inv_mapper)

        sp.save_npz("data/X.npz", X)
