from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

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

    def __str__(self):
        return self.title
    
class Rating(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner.username} : {self.value / 2}"
