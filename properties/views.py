from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PropertyForm, PropertySearchForm
from .models import Property, PropertyImage
from .querysets import with_favorite_state

LISTINGS_PER_PAGE = 12


def property_list(request, fixed_deal_type=None):
    search_data = request.GET.copy()
    search_data.setdefault("sort", "newest")
    form = PropertySearchForm(search_data, fixed_deal_type=fixed_deal_type)
    properties = (
        Property.objects.filter(status=Property.Status.APPROVED)
        .select_related("owner")
        .prefetch_related("images")
    )
    properties = with_favorite_state(properties, request.user)

    if form.is_valid():
        filters = form.cleaned_data
        keyword = filters["q"]
        if keyword:
            properties = properties.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(city__icontains=keyword)
                | Q(district__icontains=keyword)
                | Q(address__icontains=keyword)
            )

        deal_type = fixed_deal_type or filters["deal_type"]
        if deal_type:
            properties = properties.filter(deal_type=deal_type)
        if filters["property_type"]:
            properties = properties.filter(property_type=filters["property_type"])
        if filters["city"]:
            properties = properties.filter(city__icontains=filters["city"])
        if filters["district"]:
            properties = properties.filter(district__icontains=filters["district"])
        if filters["min_price"] is not None:
            properties = properties.filter(price__gte=filters["min_price"])
        if filters["max_price"] is not None:
            properties = properties.filter(price__lte=filters["max_price"])
        if filters["rooms"] is not None:
            properties = properties.filter(rooms=filters["rooms"])
        if filters["min_area"] is not None:
            properties = properties.filter(area__gte=filters["min_area"])
        if filters["max_area"] is not None:
            properties = properties.filter(area__lte=filters["max_area"])

        ordering = {
            "newest": ("-created_at", "-pk"),
            "price_asc": ("price", "pk"),
            "price_desc": ("-price", "-pk"),
            "area_asc": ("area", "pk"),
            "area_desc": ("-area", "-pk"),
        }
        properties = properties.order_by(*ordering[filters["sort"]])
    else:
        properties = properties.none()

    paginator = Paginator(properties, LISTINGS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    result_count = paginator.count
    query_params = request.GET.copy()
    query_params.pop("page", None)

    if fixed_deal_type == Property.DealType.SALE:
        page_title = "Sotuvdagi uylar"
    elif fixed_deal_type == Property.DealType.RENT:
        page_title = "Ijaradagi uylar"
    else:
        page_title = "Uy-joy e'lonlari"
    sort_key = form.cleaned_data.get("sort", "newest") if form.is_valid() else "newest"
    sort_label = dict(PropertySearchForm.SORT_CHOICES).get(sort_key, "Eng yangi")

    return render(
        request,
        "properties/list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "page_title": page_title,
            "sort_label": sort_label,
            "result_count": result_count,
            "pagination_query": query_params.urlencode(),
            "clear_url": request.path,
            "filters_expanded": any(key != "page" for key in request.GET),
        },
    )


def property_sale(request):
    return property_list(request, fixed_deal_type=Property.DealType.SALE)


def property_rent(request):
    return property_list(request, fixed_deal_type=Property.DealType.RENT)


def _editable_property_or_404(user, slug):
    properties = Property.objects.select_related("owner").prefetch_related("images")
    if not user.is_staff:
        properties = properties.filter(owner=user)
    return get_object_or_404(properties, slug=slug)


def property_detail(request, slug):
    properties = Property.objects.select_related("owner").prefetch_related("images")
    properties = with_favorite_state(properties, request.user)
    listing = get_object_or_404(
        properties,
        slug=slug,
    )
    can_view_unpublished = request.user.is_authenticated and (
        request.user.is_staff or listing.owner_id == request.user.pk
    )
    if listing.status != Property.Status.APPROVED and not can_view_unpublished:
        raise Http404

    return render(request, "properties/detail.html", {"property": listing})


@login_required
def property_create(request):
    listing = Property(owner=request.user)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=listing)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.status = Property.Status.PENDING
            listing.save()
            _save_property_images(listing, form.cleaned_data["images"])
        messages.success(request, "E'loningiz moderatsiyaga yuborildi.")
        return redirect("properties:detail", slug=listing.slug)

    return render(
        request,
        "properties/form.html",
        {"form": form, "property": listing, "is_create": True},
    )


@login_required
def property_update(request, slug):
    listing = _editable_property_or_404(request.user, slug)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=listing)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            listing = form.save(commit=False)
            listing.status = Property.Status.PENDING
            listing.reviewed_by = None
            listing.reviewed_at = None
            listing.rejection_reason = ""
            listing.save()
            _remove_selected_images(listing, request.POST.getlist("remove_images"))
            _save_property_images(listing, form.cleaned_data["images"])
        messages.success(request, "O'zgarishlar saqlandi va e'lon qayta moderatsiyaga yuborildi.")
        return redirect("properties:detail", slug=listing.slug)

    return render(
        request,
        "properties/form.html",
        {"form": form, "property": listing, "is_create": False},
    )


@login_required
def property_delete(request, slug):
    listing = _editable_property_or_404(request.user, slug)
    if request.method == "POST":
        image_files = [image.image for image in listing.images.all()]
        with transaction.atomic():
            listing.delete()
            for image_file in image_files:
                transaction.on_commit(lambda image_file=image_file: image_file.delete(save=False))
        messages.success(request, "E'lon o'chirildi.")
        return redirect("home")

    return render(request, "properties/confirm_delete.html", {"property": listing})


def _save_property_images(listing, uploaded_files):
    next_position = listing.images.count()
    for offset, uploaded_file in enumerate(uploaded_files):
        PropertyImage.objects.create(
            property=listing,
            image=uploaded_file,
            position=next_position + offset,
            alt_text=listing.title,
        )


def _remove_selected_images(listing, image_ids):
    images = PropertyImage.objects.filter(property=listing, pk__in=image_ids)
    for image in images:
        image_file = image.image
        image.delete()
        transaction.on_commit(lambda image_file=image_file: image_file.delete(save=False))