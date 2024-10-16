from django.urls import path, include

from movies import views

urlpatterns = [
    path('home', views.HomeView.as_view(), name="home"),
    path('<int:pk>', views.MovieDetailView.as_view(), name="movie_detail"),
    path('<int:pk>/rate', views.RatingAddView.as_view(), name="rating_add"),
    path('<int:pk>/unrate', views.RatingDeleteView.as_view(), name="rating_delete"),
    path('explore/', views.MovieListView.as_view(), name="movie_list"),
    path('explore/results', views.search_results_view, name="search_results"),
    path('explore/genres', views.GenreListView.as_view(), name="genre_list"),
    path('explore/recent-releases', views.RecentReleasesListView.as_view(), name="recent_releases"),
    path('explore/recently-added', views.RecentlyAddedListView.as_view(), name="recently_added"),
    path('explore/your-ratings', views.RatingListView.as_view(), name="rating_list"),
    path('explore/top-picks', views.RecommendedMovieListView.as_view(), name="recommended_movie_list"),
]
