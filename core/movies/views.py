from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count

from datetime import datetime, timedelta

from movies.models import Movie, Genre

LIST_PAGINATE_BY = 24

class MovieListView(ListView):
    model = Movie
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"
    ordering = ["id"]

class MovieDetailView(DetailView):
    model = Movie
    template_name = "movies/movie_detail.html"

class GenreListView(ListView):
    template_name = "movies/genre_List.html"
    context_object_name = 'genre_list'
    
    def get_queryset(self):
        return Genre.objects.annotate(count=Count('movie')).order_by('-count')

class MoviesByGenreListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        self.genre = get_object_or_404(Genre, name__iexact=self.kwargs["genre"])
        return self.genre.movie_set.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["browse"] = self.kwargs["genre"]
        return context

class RecentReleasesListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.filter(release_date__gte=datetime.now()-timedelta(days=3600)).order_by('-release_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_releases"] = "Recent releases"
        return context
    
class RecentlyAddedListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recently_added"] = "New additions"
        return context