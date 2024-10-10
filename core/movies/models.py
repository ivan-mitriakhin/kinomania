from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User

import numpy as np
from scipy.sparse import load_npz
from sklearn.neighbors import NearestNeighbors

PRODUCTION_STATUSES = { status.upper():status for status in [
        "Announced",
        "Pre-production",
        "Filming",
        "Post-production",
        "Completed",
        "Released",
    ]
}

class Language(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=50)
    def movie_count(self):
        return self.movie_set.count()
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Person(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    profile_path = models.CharField(max_length=32, blank=True, default="")
    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=100, unique_for_date="release_date")
    orig_title = models.CharField(max_length=100, unique_for_date="release_date")

    status = models.CharField(max_length=15, choices=PRODUCTION_STATUSES)
    release_date = models.DateField(null=True, blank=True)
    revenue = models.PositiveIntegerField(blank=True, default=0)
    budget = models.PositiveIntegerField(blank=True, default=0)

    runtime = models.PositiveSmallIntegerField(null=True, blank=True)
    spoken_langs = models.ManyToManyField(Language)

    tagline = models.CharField(max_length=100, blank=True, default="")
    overview = models.TextField(blank=True, default="")

    genres = models.ManyToManyField(Genre)

    prod_companies = models.ManyToManyField(Company)
    prod_countries = models.ManyToManyField(Country)

    cast = models.ManyToManyField(Person, related_name="cast")
    director = models.ManyToManyField(Person, related_name="director")
    cinematographer = models.ManyToManyField(Person, related_name="cinematographer")
    writer = models.ManyToManyField(Person, related_name="writer")
    producer = models.ManyToManyField(Person, related_name="producer")
    composer = models.ManyToManyField(Person, related_name="composer")

    poster_path = models.CharField(max_length=32, blank=True, default="")
    backdrop_path = models.CharField(max_length=32, blank=True, default="")

    tmdb_id = models.IntegerField(unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ratings_average = models.FloatField(blank=True, null=True, default=0)
    ratings_count = models.IntegerField(blank=True, default=0)

    def update_ratings_info(self):
        self.ratings_average = round(self.ratings.aggregate(models.Avg('value'))['value__avg'] / 2, 1) if self.ratings.count() > 0 else None
        self.ratings_count = self.ratings.count()
        self.save(update_fields=['ratings_average', 'ratings_count'])

    def similar_movies(self, k=16, metric='cosine'):
        X = load_npz("data/X.npz")
        movie_mapper = np.load("data/movie_mapper.npy", allow_pickle=True).item()
        movie_inv_mapper = np.load("data/movie_inv_mapper.npy", allow_pickle=True).item()

        X = X.T
        neighbour_ids = []

        movie_ind = movie_mapper[self.id]
        movie_vec = X[movie_ind]
        if isinstance(movie_vec, (np.ndarray)):
            movie_vec = movie_vec.reshape(1,-1)

        kNN = NearestNeighbors(n_neighbors=k+1, algorithm="brute", metric=metric)
        kNN.fit(X)
        neighbour = kNN.kneighbors(movie_vec, return_distance=False)
        neighbour_ids = [movie_inv_mapper[n] for n in neighbour[0]]
        neighbour_ids.pop(0)
        result = [Movie.objects.get(id=i) for i in neighbour_ids]
        return result
    
    def __str__(self):
        return self.title
    
class Rating(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        super().save(**kwargs)
        self.movie.update_ratings_info()

    def delete(self, **kwargs):
        super().delete(**kwargs)
        self.movie.update_ratings_info()

    def __str__(self):
        return f"{self.owner.username} : {self.value / 2}"
