from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from properties.models import Favorite, Property
from properties.querysets import with_favorite_state


@login_required
def favorite_list(request):
    properties = Property.objects.filter(
        status=Property.Status.APPROVED,
        favorite_entries__user=request.user,
    ).select_related("owner").prefetch_related("images")
    properties = with_favorite_state(properties, request.user)
    return render(request, "favorites/list.html", {"properties": properties})


@login_required
@require_POST
def toggle_favorite(request, slug):
    listing = get_object_or_404(
        Property,
        slug=slug,
        status=Property.Status.APPROVED,
    )
    favorite, created = Favorite.objects.get_or_create(user=request.user, property=listing)
    if created:
        messages.success(request, "E'lon sevimlilarga saqlandi.")
    else:
        favorite.delete()
        messages.info(request, "E'lon sevimlilardan olib tashlandi.")

    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("favorites:list")
    return redirect(next_url)