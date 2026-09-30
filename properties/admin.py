from django.contrib import admin
from django.utils import timezone

from .models import Favorite, Profile, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    fields = ("image", "alt_text", "position", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "deal_type",
        "property_type",
        "city",
        "price",
        "status",
        "reviewed_by",
        "reviewed_at",
        "is_featured",
        "created_at",
    )
    list_filter = ("status", "deal_type", "property_type", "city", "created_at")
    list_editable = ("is_featured",)
    search_fields = ("title", "slug", "city", "district", "address", "owner__username")
    readonly_fields = ("slug", "reviewed_by", "reviewed_at", "created_at", "updated_at")
    fieldsets = (
        (
            "E'lon ma'lumotlari",
            {
                "fields": (
                    "owner",
                    "title",
                    "slug",
                    "description",
                    "price",
                    "deal_type",
                    "property_type",
                    "city",
                    "district",
                    "address",
                    "area",
                    "rooms",
                    "floor",
                    "total_floors",
                    "renovation",
                    "furnished",
                    "phone",
                    "is_featured",
                )
            },
        ),
        (
            "Moderatsiya",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "reviewed_by",
                    "reviewed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    inlines = (PropertyImageInline,)
    list_select_related = ("owner",)
    list_per_page = 30
    actions = ("approve_properties", "reject_properties", "reset_to_pending")

    @admin.action(description="Tanlangan e'lonlarni tasdiqlash")
    def approve_properties(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(
            status=Property.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=now,
            rejection_reason="",
            updated_at=now,
        )
        self.message_user(request, f"{updated} ta e'lon tasdiqlandi.")

    @admin.action(description="Tanlangan e'lonlarni rad etish")
    def reject_properties(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(
            status=Property.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=now,
            rejection_reason="",
            updated_at=now,
        )
        self.message_user(request, f"{updated} ta e'lon rad etildi.")

    @admin.action(description="Tanlangan e'lonlarni qayta ko'rib chiqishga yuborish")
    def reset_to_pending(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(
            status=Property.Status.PENDING,
            reviewed_by=None,
            reviewed_at=None,
            rejection_reason="",
            updated_at=now,
        )
        self.message_user(request, f"{updated} ta e'lon kutilmoqda holatiga qaytarildi.")

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = Property.objects.only("status").get(pk=obj.pk).status

        if obj.status == Property.Status.PENDING:
            obj.reviewed_by = None
            obj.reviewed_at = None
            obj.rejection_reason = ""
        elif obj.status != previous_status:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            if obj.status == Property.Status.APPROVED:
                obj.rejection_reason = ""

        super().save_model(request, obj, form, change)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "phone")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "position", "alt_text", "created_at")
    search_fields = ("property__title", "property__slug", "alt_text")
    list_select_related = ("property",)
    readonly_fields = ("created_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
    search_fields = ("user__username", "property__title", "property__slug")
    list_select_related = ("user", "property")
    readonly_fields = ("created_at",)