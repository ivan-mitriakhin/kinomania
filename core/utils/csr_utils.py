import numpy as np
import scipy.sparse as sp
from zipfile import BadZipfile

def csr_append(X, axis=0):
        if axis not in [0, 1]:
            raise ValueError(f"No axis named { axis }, please choose between 0 and 1.")
        
        if axis == 0:
            X._shape = (X.shape[0] + 1, X.shape[1])
            X.indptr = np.hstack((X.indptr,X.indptr[-1]))
        else:
            X._shape = (X.shape[0], X.shape[1] + 1)

        sp.save_npz("data/X.npz", X)
