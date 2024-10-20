import unicodedata
import pandas as pd
import requests
import os

from django.db.models import signals

from movies.models import Language, Genre, Company, Country, Person, Movie, update_X

def strip_accents(text):
    return ''.join(char for char in
                   unicodedata.normalize('NFKD', text)
                   if unicodedata.category(char) != 'Mn')

def process_objects(objs, model):
    result = []

    if not objs:
        return result

    for obj in objs:
        name = obj["name"].strip().title()
        obj, _ = model.objects.get_or_create(name=name)
        result.append(obj)

    return result

def process_persons(objs, job=None):
    result = []

    if not objs:
        return result
    
    for obj in objs:
        if job and (obj["job"].lower() not in job):
            continue
        name = strip_accents(obj["name"].strip().title())
        tmdb_id = obj["id"]
        profile_path = obj.get("profile_path")
        obj, created = Person.objects.get_or_create(tmdb_id=tmdb_id, name=name)
        if created and profile_path:
            obj.profile_path = profile_path
            obj.save()
        result.append(obj)

    return result

def get_default_if_none(data, field, model):
    value = data.get(field)
    return value if value else model._meta.get_field(field).get_default()

def run():
    signals.post_save.disconnect(receiver=update_X, sender=Movie)

    movies = pd.read_csv("movies.csv")

    for _, movie in movies.iterrows():
        tmdb_id = movie.tmdbId

        if Movie.objects.filter(tmdb_id=tmdb_id).exists():
            continue

        movie_data = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={os.getenv('TMDB_KEY')}&language=en-US").json()
        if not movie_data.get('success', True):
            continue

        credit_data = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={os.getenv('TMDB_KEY')}&language=en-US").json()
        cast_data = credit_data.get('cast')
        crew_data = credit_data.get('crew')

        title = movie_data["title"]
        orig_title = movie_data["original_title"]
        status = movie_data["status"]
        release_date = movie_data.get("release_date")
        runtime = movie_data.get("runtime")

        if status == "Released" and not release_date:
            continue

        revenue = get_default_if_none(movie_data, "revenue", Movie)
        budget = get_default_if_none(movie_data, "budget", Movie)
        tagline = get_default_if_none(movie_data, "tagline", Movie)
        overview = get_default_if_none(movie_data, "overview", Movie)
        poster_path = get_default_if_none(movie_data, "poster_path", Movie)
        backdrop_path = get_default_if_none(movie_data, "backdrop_path", Movie)

        m = Movie(
            title=title,
            orig_title=orig_title,
            status=status,
            release_date=release_date,
            revenue=revenue,
            budget=budget,
            runtime=runtime,
            tagline=tagline,
            overview=overview,
            tmdb_id=tmdb_id,
            poster_path=poster_path,
            backdrop_path=backdrop_path,
        )
        m.save()

        spoken_langs = process_objects(movie_data.get("spoken_languages"), Language)
        genres = process_objects(movie_data.get("genres"), Genre)
        prod_companies = process_objects(movie_data.get("production_companies"), Company)
        prod_countries = process_objects(movie_data.get("production_countries"), Country)

        cast = process_persons(cast_data)
        director = process_persons(crew_data, ["director", "co-director"])
        cinematographer = process_persons(crew_data, ["director of photography"])
        writer = process_persons(crew_data, ["screenplay", "novel"])
        producer = process_persons(crew_data, ["producer", "associate producer", "executive producer"])
        composer = process_persons(crew_data, ["original music composer"])

        m.spoken_langs.add(*spoken_langs)
        m.genres.add(*genres)
        m.prod_companies.add(*prod_companies)
        m.prod_countries.add(*prod_countries)
        m.cast.add(*cast)
        m.director.add(*director)
        m.cinematographer.add(*cinematographer)
        m.writer.add(*writer)
        m.producer.add(*producer)
        m.composer.add(*composer)




