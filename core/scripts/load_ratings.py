import pandas as pd
from faker import Faker

from django.contrib.auth.models import User

from movies.models import Rating, Movie

"""
A script to populate database with real user ratings
of different movies obtained from Movielens' 20M 
dataset. As the real users' data is not available
it is decided to populate it with fake data.
"""

def username_exists(username):
    return User.objects.filter(username=username).exists()

def run():
    ratings = pd.read_csv("ratings.csv")
    user_ids = ratings.userId.unique()
    users_cnt = len(User.objects.all())

    for idx, user_id in enumerate(user_ids, 1):
        if idx <= users_cnt:
            continue
        fake = Faker()
        fake.seed_instance(user_id) 
        username = fake.user_name()
        password = fake.password()
        while username_exists(username):
            username = fake.user_name()

        user = User.objects.create_user(username=username, password=password)
        
        user_ratings = []
        for _, rating in ratings[ratings.userId == user_id].iterrows():
            tmdb_id = int(rating.tmdbId)
            if not Movie.objects.filter(tmdb_id=tmdb_id).exists():
                continue
            value = int(rating.rating * 2)
            movie = Movie.objects.get(tmdb_id=tmdb_id)
            r = Rating(owner=user, movie=movie, value=value)
            user_ratings.append(r)
        
        Rating.objects.bulk_create(user_ratings)
            