import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix, save_npz

from movies.models import Rating

def run():
        """
        Generates a sparse matrix from ratings dataframe.
        
        Args:
            df: pandas dataframe containing 3 columns (owner_id, movie_id, value)
        
        Returns:
            X: sparse matrix
            user_mapper: dict that maps user id's to user indices
            user_inv_mapper: dict that maps user indices to user id's
            movie_mapper: dict that maps movie id's to movie indices
            movie_inv_mapper: dict that maps movie indices to movie id's
        """

        df = pd.DataFrame.from_records(Rating.objects.all().values("owner_id", "movie_id", "value"))

        M = df['owner_id'].nunique()
        N = df['movie_id'].nunique()

        user_mapper = dict(zip(np.unique(df["owner_id"]), list(range(M))))
        movie_mapper = dict(zip(np.unique(df["movie_id"]), list(range(N))))
        
        user_inv_mapper = dict(zip(list(range(M)), np.unique(df["owner_id"])))
        movie_inv_mapper = dict(zip(list(range(N)), np.unique(df["movie_id"])))
        
        user_index = [user_mapper[i] for i in df['owner_id']]
        item_index = [movie_mapper[i] for i in df['movie_id']]

        X = csr_matrix((df["value"], (user_index,item_index)), shape=(M,N))

        save_npz("data/X.npz", X)
        np.save("data/user_mapper.npy", user_mapper)
        np.save("data/movie_mapper.npy", movie_mapper)
        np.save("data/user_inv_mapper.npy", user_inv_mapper)
        np.save("data/movie_inv_mapper.npy", movie_inv_mapper)
        