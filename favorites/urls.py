from django.urls import path

from . import views

app_name = "favorites"

urlpatterns = [
    path("favorites/", views.favorite_list, name="list"),
    path("favorites/toggle/<slug:slug>/", views.toggle_favorite, name="toggle"),
]