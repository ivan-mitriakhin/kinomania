from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count

from datetime import datetime, timedelta

from movies.models import Movie, Genre, Rating, MyUser

LIST_PAGINATE_BY = 24

"""
MOVIE
"""

class MovieListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        ordering = self.request.GET.get("ordering", "ratings_count")
        search = self.request.GET.get("search")
        if not ordering:
            ordering = "ratings_count"
        genre = self.request.GET.get("genre")
        queryset = None

        if search:
            queryset = Movie.objects.filter(title__icontains=search)
        else:
            queryset = Movie.objects.all()

        if genre:
            queryset = queryset.filter(genres__in=[Genre.objects.get(name__iexact=genre)])

        if ordering == "recommend" and self.request.user.is_authenticated:
            user = MyUser.objects.get(pk=self.request.user.pk)
            return user.recommend_movies(queryset)
        else:
            return queryset.order_by("-" + ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get("search")
        genre = self.request.GET.get("genre")

        if search:
            context["header"] = {"side": "you searched for titles like", "main": search}
        else:
            context["header"] = {"side": " ", "main": "all movies"}
        
        if genre:
            context["header"] = {"side": "browsing by genre", "main": genre.lower()}

        context["ordering"] = True

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

class RecommendedMovieListView(LoginRequiredMixin, ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"
    login_url = '/profile/login/'

    def get_queryset(self):
        user = MyUser.objects.get(pk=self.request.user.pk)
        return user.recommended_movies()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "movies recommended specifically to you", "main": "top picks"}
        context["ordering"] = False
        return context

class RecentReleasesListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.filter(release_date__gte=datetime.now()-timedelta(days=3600)).order_by('-release_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "movies released in last 3600 days", "main": "recent releases"}
        context["ordering"] = False
        return context
    
class RecentlyAddedListView(ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/movie_list.html"

    def get_queryset(self):
        return Movie.objects.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = {"side": "movies recently added", "main": "new additions"}
        context["ordering"] = False
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

class RatingListView(LoginRequiredMixin, ListView):
    paginate_by = LIST_PAGINATE_BY
    template_name = "movies/rating_list.html"

    def get_queryset(self):
        ordering = self.request.GET.get("ordering", "rating")
        if not ordering:
            ordering = "rating"

        owner = self.request.user
        queryset = Rating.objects.filter(owner=owner)
        
        if ordering == "rating":
            return queryset.order_by("-value")
        else:
            return queryset.order_by("-movie__" + ordering)

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