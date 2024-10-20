from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

import pandas as pd
import numpy as np
import scipy.sparse as sp
from sklearn.neighbors import NearestNeighbors

from utils.csr_utils import load_X, csr_append

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
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=255)
    def movie_count(self):
        return self.movie_set.count()
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Person(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    profile_path = models.CharField(max_length=32, blank=True, default="")
    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255, unique_for_date="release_date")
    orig_title = models.CharField(max_length=255, unique_for_date="release_date")

    status = models.CharField(max_length=15, choices=PRODUCTION_STATUSES)
    release_date = models.DateField(null=True, blank=True)
    revenue = models.PositiveBigIntegerField(blank=True, default=0)
    budget = models.PositiveIntegerField(blank=True, default=0)

    runtime = models.PositiveSmallIntegerField(null=True, blank=True)
    spoken_langs = models.ManyToManyField(Language)

    tagline = models.CharField(max_length=255, blank=True, default="")
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
        X = load_X()

        X = X.T
        neighbour_ids = []

        movie_vec = X[self.id - 1]
        if isinstance(movie_vec, (np.ndarray)):
            movie_vec = movie_vec.reshape(1,-1)

        kNN = NearestNeighbors(n_neighbors=k+1, algorithm="brute", metric=metric)
        kNN.fit(X)
        neighbour = kNN.kneighbors(movie_vec, return_distance=False)
        neighbour_ids = [i + 1 for i in neighbour[0]]
        neighbour_ids.pop(0)
        result = [Movie.objects.get(id=i) for i in neighbour_ids]
        return result
    
    def __str__(self):
        return self.title
    
class Rating(models.Model):
    class Meta:
        unique_together = ('owner', 'movie')

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def csr_update(self, save=True):
        X = load_X()
        movie_mapper = np.load("data/movie_mapper.npy", allow_pickle=True).item()
        user_mapper = np.load("data/user_mapper.npy", allow_pickle=True).item()
        i = user_mapper[self.owner.pk]
        j = movie_mapper[self.movie.pk]
        if save:
            X[i, j] = self.value
        else:
            X[i, j] = 0
            X.eliminate_zeros()
        sp.save_npz("data/X.npz", X)

    def save(self, **kwargs):
        super().save(**kwargs)
        self.movie.update_ratings_info()
        self.csr_update(save=True)

    def delete(self, **kwargs):
        super().delete(**kwargs)
        self.movie.update_ratings_info()
        self.csr_update(save=False)

    def __str__(self):
        return f"{self.owner.username} : {self.value / 2}"

class MyUser(User):
    class Meta:
        proxy = True

    def recommended_movies(self, num_similar_users=100):
        X = load_X()

        # Converting to mean-centered matrix (subtracting means of each row) 
        total_vec = np.array(X.sum(axis=1).squeeze())[0]
        counts_vec = np.diff(X.indptr)
        mean_vec = total_vec / counts_vec
        diag_mean_matrix = sp.diags(mean_vec, 0)
        util_matrix = X.copy()
        util_matrix.data = np.ones_like(util_matrix.data)
        mean_matrix = diag_mean_matrix * util_matrix # Each row's non-zero elements are equal to the mean
        X = X - mean_matrix

        user_vec = X[self.pk - 1]       
        if isinstance(user_vec, (np.ndarray)):
            user_vec = user_vec.reshape(1,-1)

        # Picking 100 similar users for now
        kNN = NearestNeighbors(n_neighbors=num_similar_users+1, algorithm="brute", metric="cosine")
        kNN.fit(X)
        neighbour = kNN.kneighbors(user_vec)
        # Not taking first element as it is the user themselves 
        neighbour_ids = neighbour[1].flatten()[1:]
        distances = dict(zip(neighbour_ids, neighbour[0].flatten()[1:]))

        # Finding all movies that were rated by the user
        watched_movies = [r.movie.id - 1 for r in self.ratings.all()]

        # Selected user-movie matrix
        similar_user_movies = [X[i].todense() for i in neighbour_ids]
        similar_user_movies = pd.DataFrame(np.array(similar_user_movies).reshape(num_similar_users, -1), index=neighbour_ids)

        # Deleting movies that were rated by the user
        similar_user_movies = similar_user_movies[similar_user_movies.columns.difference(watched_movies)]
        
        # Removing movies that weren't rated by any of the selected users
        similar_user_movies = similar_user_movies.loc[:, (similar_user_movies != 0).any(axis=0)]

        movie_score = []

        for i in similar_user_movies.columns:
            # Get the ratings for movie i
            movie_ratings = similar_user_movies.loc[:, i]
            scores = []
            for n in neighbour_ids:
                rating = movie_ratings[n]
                sim_score = distances[n]
                if rating != 0:
                    score = sim_score * rating
                    scores.append(score)
            movie_score.append( (i, np.mean(scores)) )

        # Sorting movie-score array by score and picking k of them
        movie_score = sorted(movie_score, key=lambda x: x[1], reverse=True)
        result = [Movie.objects.get(id=i+1) for i, _ in movie_score]
        return result

@receiver(post_save, sender=MyUser)
def update_X(sender, instance, created, **kwargs):
    if created:
        csr_append(instance, axis=0)

@receiver(post_save, sender=Movie)
def update_X(sender, instance, created, **kwargs):
    if created:
        csr_append(instance, axis=1)