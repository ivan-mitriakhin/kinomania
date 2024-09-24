import pandas as pd
import langcodes

from movies.models import Language, Genre, Company, Country, Human, Movie

def process_objects(objs, model):
    result = []

    if type(objs) != str:
        return result

    for obj in objs.split(','):
        obj = obj.strip().title()
        obj, _ = model.objects.get_or_create(name=obj)
        result.append(obj)

    return result

def lang_code_to_name(lang):
    if not lang or lang.lower() == "no language":
        return "—"
    
    return langcodes.Language.get(lang).autonym().title()

def run():
    movies = pd.read_csv('movies.csv')
    
    Language.objects.all().delete()
    Genre.objects.all().delete()
    Company.objects.all().delete()
    Country.objects.all().delete()
    Human.objects.all().delete()
    Movie.objects.all().delete()

    for _, movie in movies.where(pd.notnull(movies), None).iterrows():
        title = movie.title
        orig_title = movie.original_title
        status = movie.status
        revenue = movie.revenue
        budget = movie.budget
        runtime = movie.runtime
        tagline = movie.tagline
        overview = movie.overview
        tmdb_id = movie.id
        imdb_id = movie.imdb_id
        release_date = movie.release_date
        
        orig_lang, _ = Language.objects.get_or_create(
            name=lang_code_to_name(movie.original_language)
        )

        m = Movie(
            title=title,
            orig_title=orig_title,
            status=status,
            release_date=release_date,
            revenue=revenue,
            budget=budget,
            runtime=runtime,
            orig_lang=orig_lang,
            tagline=tagline,
            overview=overview,
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
        )
        m.save()

        spoken_langs = process_objects(movie.spoken_languages, Language)
        genres = process_objects(movie.genres, Genre)
        prod_companies = process_objects(movie.production_companies, Company)
        prod_countries = process_objects(movie.production_countries, Country)
        cast = process_objects(movie.cast, Human)
        directors = process_objects(movie.director, Human)
        dop = process_objects(movie.director_of_photography, Human)
        writers = process_objects(movie.writers, Human)
        producers = process_objects(movie.producers, Human)
        composers = process_objects(movie.music_composer, Human)

        m.spoken_langs.add(*spoken_langs)
        m.genres.add(*genres)
        m.prod_companies.add(*prod_companies)
        m.prod_countries.add(*prod_countries)
        m.cast.add(*cast)
        m.directors.add(*directors)
        m.dop.add(*dop)
        m.writers.add(*writers)
        m.producers.add(*producers)
        m.composers.add(*composers)




