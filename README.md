# **Kinomania**: A Movie Recommendation System

Kinomania is a movie recommender web application that is based on collaborative filtering approach and is heavily inspired by [MovieLens](https://movielens.org/home). It utilizes methods provided by [implicit](https://github.com/benfred/implicit) library. To populate the database [MovieLens 20M dataset](https://grouplens.org/datasets/movielens/20m/) (20 million ratings applied to 27,000 movies by 138,000 users) was used. Celery (with Redis as message broker) is needed to offload long-running machine learning work from the main request/response cycle within Django to enhance user experience.

## Run locally

```
git clone https://github.com/ivan-mitriakhin/kinomania.git

cd kinomania

cd core
```

There create a .env file:

```
SECRET_KEY=<your-secret-key>
POSTGRES_DB=kinomania
POSTGRES_NAME=kinomania
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432  
CELERY_BROKER_URL=redis://redis:6379/0
REDIS_BACKEND=redis://redis:6379/0
OPENBLAS_NUM_THREADS=1
```

Build with docker compose:
```
cd ..

docker-compose build

docker-compose up
```

Then, in order to populate the database:

```
docker exec -it kinomania-db-1 bash

psql -U postgres kinomania < kinomania.sql

exit

docker-compose down

docker-compose up
```
Now, it is all ready at [localhost](localhost).