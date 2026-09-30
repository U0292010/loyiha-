from django.urls import path

from .views import UyTopLoginView, UyTopLogoutView, profile, register

app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", UyTopLoginView.as_view(), name="login"),
    path("logout/", UyTopLogoutView.as_view(), name="logout"),
    path("profile/", profile, name="profile"),
]