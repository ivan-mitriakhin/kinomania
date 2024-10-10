from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count

from datetime import datetime, timedelta

from movies.models import Movie, Genre, Rating

LIST_PAGINATE_BY = 24

"""
MOVIE
"""

class MovieListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        search = self.request.GET.get("search")
        ordering = self.request.GET.get("ordering", "ratings_count")
        queryset = None
        if search:
            queryset = Movie.objects.filter(title__icontains=search)
        else:
            queryset = Movie.objects.all()

        return queryset.order_by("-" + ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get("search")
        if search:
            context["header"] = {"side": "you searched for titles like", "main": search}
        else:
            context["header"] = {"side": " ", "main": "all movies"}
        return context

class MovieDetailView(DetailView):
    model = Movie
    template_name = "movies/movie_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and Rating.objects.filter(movie=context["movie"], owner=self.request.user).exists():
            value = Rating.objects.get(movie=context["movie"], owner=self.request.user).value
            context["user_rating"] = value
        return context

class MoviesByGenreListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        self.genre = get_object_or_404(Genre, name__iexact=self.kwargs["genre"])
        return self.genre.movie_set.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "browse by", "main": self.kwargs["genre"]}
        return context

class RecentReleasesListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.filter(release_date__gte=datetime.now()-timedelta(days=3600)).order_by('-release_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "movies released in last 3600 days", "main": "recent releases"}
        return context
    
class RecentlyAddedListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "movies recently added", "main": "new additions"}
        return context
    
def search_results_view(request):
    query = request.GET.get('search', '')
    movies = []
    if query:
        movies = Movie.objects.filter(title__icontains=query)
    context = {'movies': movies}
    return render(request, 'movies/search_results.html', context)
    
"""
RATING
"""
    
class RatingAddView(LoginRequiredMixin, View):
    def post(self, request, pk):
        value = int(request.POST['rating'])
        movie = Movie.objects.get(pk=pk)
        owner = request.user
        r, _ = Rating.objects.get_or_create(movie=movie, owner=owner)
        r.value = value
        r.save()
        return redirect(reverse('movie_detail', args=[pk]))
    
class RatingDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        movie = Movie.objects.get(pk=pk)
        owner = request.user
        r = Rating.objects.get(movie=movie, owner=owner)
        r.delete()
        return redirect(reverse('movie_detail', args=[pk]))
    
"""
GENRE
"""

class GenreListView(ListView):
    template_name = "movies/genre_list.html"
    context_object_name = 'genre_list'
    
    def get_queryset(self):
        return Genre.objects.annotate(count=Count('movie')).order_by('-count')