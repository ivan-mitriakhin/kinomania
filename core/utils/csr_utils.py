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
        
        if axis == 0:
            X._shape = (X.shape[0] + 1, X.shape[1])
            X.indptr = np.hstack((X.indptr,X.indptr[-1]))
        else:
            X._shape = (X.shape[0], X.shape[1] + 1)

        sp.save_npz("data/X.npz", X)
