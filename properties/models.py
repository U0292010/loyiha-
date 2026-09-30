from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=24, blank=True)
    avatar = models.ImageField(upload_to="profiles/%Y/%m/", blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil: {self.user}"


class Property(models.Model):
    class DealType(models.TextChoices):
        SALE = "sale", "Sotish"
        RENT = "rent", "Ijara"

    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Kvartira"
        HOUSE = "house", "Uy"
        LAND = "land", "Yer"
        OFFICE = "office", "Ofis"
        COMMERCIAL = "commercial", "Tijorat"

    class Renovation(models.TextChoices):
        NEW = "new", "Yangi qurilgan"
        EURO = "euro", "Yevro ta'mir"
        GOOD = "good", "Yaxshi"
        NEEDS_REPAIR = "needs_repair", "Ta'mir talab"
        SHELL = "shell", "Qora suvoq"

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="properties",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    deal_type = models.CharField(max_length=8, choices=DealType.choices)
    property_type = models.CharField(max_length=12, choices=PropertyType.choices)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    area = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    rooms = models.PositiveSmallIntegerField(null=True, blank=True)
    floor = models.PositiveSmallIntegerField(null=True, blank=True)
    total_floors = models.PositiveSmallIntegerField(null=True, blank=True)
    renovation = models.CharField(max_length=16, choices=Renovation.choices)
    furnished = models.BooleanField(default=False)
    phone = models.CharField(max_length=24)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_properties",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="property_status_created"),
            models.Index(
                fields=["deal_type", "property_type", "city"],
                name="property_search_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="property_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(area__gt=0),
                name="property_area_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(floor__isnull=True)
                    | Q(total_floors__isnull=True)
                    | Q(floor__lte=models.F("total_floors"))
                ),
                name="property_floor_within_total",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:200] or "property"
            candidate = base_slug
            suffix = 2
            while Property.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                suffix_text = f"-{suffix}"
                candidate = f"{base_slug[: 220 - len(suffix_text)]}{suffix_text}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="properties/%Y/%m/")
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "pk"]
        indexes = [
            models.Index(fields=["property", "position"], name="property_image_order_idx"),
        ]

    def __str__(self):
        return f"{self.property}: rasm {self.position + 1}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="favorite_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property"],
                name="favorite_unique_user_property",
            ),
        ]

    def __str__(self):
        return f"{self.user}: {self.property}"