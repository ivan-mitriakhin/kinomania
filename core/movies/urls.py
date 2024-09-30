from django.urls import path, include

from movies import views

urlpatterns = [
    path('', views.MovieListView.as_view(), name="movie_list"),
    path('<int:pk>', views.MovieDetailView.as_view(), name="movie_detail"),
]