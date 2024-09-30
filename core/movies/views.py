from django.views import View
from django.core.paginator import Paginator
from django.shortcuts import render

import requests
import os

from movies.models import Movie

class MovieListView(View):
    def get(self, request):
        movie_list = Movie.objects.all()
        paginator = Paginator(movie_list, 30)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(request, "movies/movie_list.html", {"page_obj": page_obj})
