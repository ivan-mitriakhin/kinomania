from django.views import View
from django.views.generic import ListView, DetailView

from movies.models import Movie

class MovieListView(ListView):
    model = Movie
    paginate_by = 24
    template_name = "movies/movie_list.html"
    ordering = ["id"]

class MovieDetailView(DetailView):
    model = Movie
    template_name = "movies/movie_detail.html"