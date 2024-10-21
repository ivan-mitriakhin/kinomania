from django.apps import AppConfig
import implicit
import scipy.sparse as sp

class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'

    X = sp.load_npz("data/X.npz")
    knn_model = implicit.nearest_neighbours.CosineRecommender.load("data/knn_model.npz")
    als_model = implicit.cpu.als.AlternatingLeastSquares.load("data/als_model.npz")
