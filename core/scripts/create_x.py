import connectorx as cx
import numpy as np
from scipy.sparse import csr_matrix, save_npz

from movies.models import Rating, Movie, MyUser

CONNECTION = 'sqlite://db.sqlite3'

def run():
        """
        Generates a sparse user-item matrix from ratings dataframe. 
        IMPORTANT: Use this script only to generate a new matrix as
        it takes a lot of time to create it. If you're trying
        to extend the matrix with new rows (users) or columns (items)
        the util method csr_append() is used.
        
        Returns:
            X: sparse matrix
            user_mapper: dict that maps user id's to user indices
            user_inv_mapper: dict that maps user indices to user id's
            movie_mapper: dict that maps movie id's to movie indices
            movie_inv_mapper: dict that maps movie indices to movie id's
        """

        query = str(Rating.objects.all().values("owner_id", "movie_id", "value").query)
        df = cx.read_sql(CONNECTION, query)

        M = MyUser.objects.count()
        N = Movie.objects.count()

        user_index = [i - 1 for i in df['owner_id']]
        item_index = [i - 1 for i in df['movie_id']]

        X = csr_matrix((df["value"], (user_index,item_index)), shape=(M,N), dtype=np.int8)

        save_npz("data/X.npz", X)
        