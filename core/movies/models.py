from django.db import models

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

class Human(models.Model):
    name = models.CharField(max_length=50)
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
    orig_lang = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="orig_lang")
    spoken_langs = models.ManyToManyField(Language, related_name="spoken_langs")

    tagline = models.CharField(max_length=100, null=True, blank=True, default="")
    overview = models.TextField(null=True, blank=True, default="")

    genres = models.ManyToManyField(Genre)

    prod_companies = models.ManyToManyField(Company, related_name="prod_companies")
    prod_countries = models.ManyToManyField(Country, related_name="prod_countries")

    cast = models.ManyToManyField(Human, related_name="cast")
    directors = models.ManyToManyField(Human, related_name="directors")
    dop = models.ManyToManyField(Human, related_name="dop")
    writers = models.ManyToManyField(Human, related_name="writers")
    producers = models.ManyToManyField(Human, related_name="producers")
    composers = models.ManyToManyField(Human, related_name="composers")

    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=10, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title