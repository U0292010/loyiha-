from django.urls import path

from . import views

app_name = "properties"

urlpatterns = [
    path("properties/", views.property_list, name="list"),
    path("properties/sale/", views.property_sale, name="sale"),
    path("properties/rent/", views.property_rent, name="rent"),
    path("properties/create/", views.property_create, name="create"),
    path("properties/<slug:slug>/", views.property_detail, name="detail"),
    path("properties/<slug:slug>/edit/", views.property_update, name="edit"),
    path("properties/<slug:slug>/delete/", views.property_delete, name="delete"),
]