from django.shortcuts import render

from properties.models import Property
from properties.querysets import with_favorite_state


def home(request):
    approved_properties = Property.objects.filter(
        status=Property.Status.APPROVED,
    ).prefetch_related("images")
    approved_properties = with_favorite_state(approved_properties, request.user)
    featured_properties = approved_properties.filter(is_featured=True)[:3]
    latest_properties = approved_properties[:6]

    return render(
        request,
        "home.html",
        {
            "featured_properties": featured_properties,
            "latest_properties": latest_properties,
        },
    )