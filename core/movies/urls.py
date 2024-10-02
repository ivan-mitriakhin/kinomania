from django.urls import path, include

from movies import views

urlpatterns = [
    path('', views.MovieListView.as_view(), name="movie_list"),
    path('<int:pk>', views.MovieDetailView.as_view(), name="movie_detail"),
    path('explore/genres', views.GenreListView.as_view(), name="genre_list"),
    path('explore/genres/<str:genre>', views.MoviesByGenreListView.as_view(), name="movies_by_genre"),
    path('explore/recent-releases', views.RecentReleasesListView.as_view(), name="recent_releases"),
    path('explore/recently-added', views.RecentlyAddedListView.as_view(), name="recently_added"),
]
