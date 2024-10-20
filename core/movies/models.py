from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

import implicit
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

    bayesian_average = models.FloatField(blank=True, null=True, default=0)
    ratings_average = models.FloatField(blank=True, null=True, default=0)
    ratings_count = models.IntegerField(blank=True, default=0)

    def update_ratings_info(self):
        # https://en.wikipedia.org/wiki/Bayesian_average
        C = Movie.objects.aggregate(models.Avg('ratings_count'))['ratings_count__avg']
        m = Movie.objects.aggregate(models.Avg('ratings_average'))['ratings_average__avg']
        count = self.ratings.count()
        sum = self.ratings.aggregate(models.Sum('value'))['value__sum'] / 2

        self.ratings_count = count
        self.bayesian_average = (C * m + sum) / (C + count) if count > 0 else None
        self.ratings_average = self.ratings.aggregate(models.Avg('value'))['value__avg'] / 2 if count > 0 else None
        self.save(update_fields=['bayesian_average', 'ratings_average', 'ratings_count'])

    def similar_movies(self, N=16):
        X = load_X()

        model = implicit.nearest_neighbours.CosineRecommender()
        model.fit(X, show_progress=False)
        items_scores = model.similar_items(itemid=self.pk-1, N=N)
        similar_items = items_scores[0][1:] # Not including the object itself
        
        result = [Movie.objects.get(id=i+1) for i in similar_items]
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
        i = self.owner.pk - 1
        j = self.movie.pk - 1
        if save:
            X[i, j] = self.value
        else:
            X[i, j] = 0
            X.eliminate_zeros()

        knn_model = implicit.nearest_neighbours.CosineRecommender.load("data/knn_model")
        als_model = implicit.cpu.als.AlternatingLeastSquares.load("data/als_model")
        knn_model.fit(X)
        als_model.partial_fit_users([i], X[i])
        als_model.partial_fit_items([j], X.T[j])
        knn_model.save('data/knn_model')
        als_model.save('data/als_model')

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
    
class Recommend(models.Model):
    class RecommenderType(models.IntegerChoices):
        NON_PERSONALIZED = 1
        PERSONALIZED_1 = 2
        PERSONALIZED_2 = 3

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recommender_type = models.PositiveSmallIntegerField(choices=RecommenderType, default=RecommenderType.NON_PERSONALIZED)

    def recommended_movies(self, N=1000):
        if self.recommender_type == self.RecommenderType.NON_PERSONALIZED:
            return Movie.objects.order_by(models.F('bayesian_average').desc(nulls_last=True))[:N]
        
        model = None
        if self.recommender_type == self.RecommenderType.PERSONALIZED_1:
            model = implicit.nearest_neighbours.CosineRecommender()
        elif self.recommender_type == self.RecommenderType.PERSONALIZED_2:
            model = implicit.cpu.als.AlternatingLeastSquares(factors=50)

        X = load_X()
        model.fit(X, show_progress=False)
        X.dtype = np.float32
        id = self.user.pk - 1
        items_scores = model.recommend(id, X[id], N=N)
        recommended_items = items_scores[0]

        result = [Movie.objects.get(id=i+1) for i in recommended_items]
        return result

@receiver(post_save, sender=User)
def create_recommend(sender, instance, created, **kwargs):
    if created:
        r = Recommend(user=instance,
                      recommender_type=instance.RecommenderType.NON_PERSONALIZED)
        r.save()

@receiver(post_save, sender=User)
def update_X(sender, instance, created, **kwargs):
    if created:
        csr_append(axis=0)

@receiver(post_save, sender=Movie)
def update_X(sender, instance, created, **kwargs):
    if created:
        csr_append(axis=1)