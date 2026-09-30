from django.db.models import BooleanField, Exists, OuterRef, Value

from .models import Favorite


def with_favorite_state(queryset, user):
    if not user.is_authenticated:
        return queryset.annotate(is_favorited=Value(False, output_field=BooleanField()))

    user_favorites = Favorite.objects.filter(user=user, property_id=OuterRef("pk"))
    return queryset.annotate(is_favorited=Exists(user_favorites))