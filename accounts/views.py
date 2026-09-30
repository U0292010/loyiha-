from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import redirect, render

from properties.models import Profile

from .forms import (
    AccountUpdateForm,
    ProfileUpdateForm,
    RegistrationForm,
    UyTopAuthenticationForm,
)


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user)
        messages.success(request, "Hisobingiz yaratildi. Endi tizimga kiring.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


class UyTopLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = UyTopAuthenticationForm
    redirect_authenticated_user = True


class UyTopLogoutView(LogoutView):
    http_method_names = ["post", "options"]


@login_required
def profile(request):
    profile_record, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        account_form = AccountUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile_record,
        )
        if account_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                account_form.save()
                profile_form.save()
            messages.success(request, "Profil ma'lumotlari saqlandi.")
            return redirect("accounts:profile")
    else:
        account_form = AccountUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_record)

    return render(
        request,
        "accounts/profile.html",
        {"account_form": account_form, "profile_form": profile_form},
    )