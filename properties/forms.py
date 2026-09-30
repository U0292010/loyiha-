from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput

from .models import Property

MAX_PROPERTY_IMAGES = 10
MAX_IMAGE_SIZE = 10 * 1024 * 1024


class MultipleImageInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        if not data:
            return []

        uploaded_files = data if isinstance(data, (list, tuple)) else [data]
        cleaned_files = [super(MultipleImageField, self).clean(file) for file in uploaded_files]
        if any(file.size > MAX_IMAGE_SIZE for file in cleaned_files):
            raise ValidationError("Har bir rasm hajmi 10 MB dan oshmasligi kerak.")
        return cleaned_files


class PropertyForm(forms.ModelForm):
    images = MultipleImageField(
        required=False,
        label="Uy rasmlari",
        help_text="PNG, JPG yoki GIF. Ko'pi bilan 10 ta rasm, har biri 10 MB gacha.",
        widget=MultipleImageInput(attrs={"accept": "image/*"}),
    )

    class Meta:
        model = Property
        fields = (
            "title",
            "description",
            "deal_type",
            "property_type",
            "price",
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
            "images",
        )
        labels = {
            "title": "E'lon sarlavhasi",
            "description": "Tavsif",
            "deal_type": "E'lon turi",
            "property_type": "Uy turi",
            "price": "Narx (so'm)",
            "city": "Shahar",
            "district": "Tuman",
            "address": "Manzil",
            "area": "Maydon (m²)",
            "rooms": "Xonalar soni",
            "floor": "Qavat",
            "total_floors": "Jami qavatlar",
            "renovation": "Ta'mirlash holati",
            "furnished": "Jihozlangan",
            "phone": "Telefon raqami",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "area": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "rooms": forms.NumberInput(attrs={"min": "0", "step": "1"}),
            "floor": forms.NumberInput(attrs={"min": "0", "step": "1"}),
            "total_floors": forms.NumberInput(attrs={"min": "0", "step": "1"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def clean_images(self):
        uploaded_files = self.cleaned_data["images"]
        existing_count = 0

        if self.instance.pk:
            existing_images = self.instance.images.all()
            removed_ids = self.data.getlist("remove_images")
            existing_count = existing_images.exclude(pk__in=removed_ids).count()

        if existing_count + len(uploaded_files) > MAX_PROPERTY_IMAGES:
            raise ValidationError("Bitta e'longa ko'pi bilan 10 ta rasm qo'shish mumkin.")
        return uploaded_files

    def clean(self):
        cleaned_data = super().clean()
        floor = cleaned_data.get("floor")
        total_floors = cleaned_data.get("total_floors")
        if floor is not None and total_floors is not None and floor > total_floors:
            self.add_error("floor", "Qavat jami qavatlar sonidan katta bo'lmasligi kerak.")
        return cleaned_data


class PropertySearchForm(forms.Form):
    SORT_CHOICES = (
        ("newest", "Eng yangi"),
        ("price_asc", "Narx: arzonidan"),
        ("price_desc", "Narx: qimmatidan"),
        ("area_desc", "Maydon: kattasidan"),
        ("area_asc", "Maydon: kichigidan"),
    )

    q = forms.CharField(
        required=False,
        max_length=100,
        label="Kalit so'z",
        widget=forms.SearchInput(attrs={"placeholder": "Sarlavha yoki manzil"}),
    )
    deal_type = forms.ChoiceField(
        required=False,
        choices=(("", "Sotish yoki ijara"), *Property.DealType.choices),
        label="E'lon turi",
    )
    property_type = forms.ChoiceField(
        required=False,
        choices=(("", "Barcha uy turlari"), *Property.PropertyType.choices),
        label="Uy turi",
    )
    city = forms.CharField(required=False, max_length=100, label="Shahar")
    district = forms.CharField(required=False, max_length=100, label="Tuman")
    min_price = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=14,
        decimal_places=2,
        label="Narx, dan",
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=14,
        decimal_places=2,
        label="Narx, gacha",
    )
    rooms = forms.IntegerField(required=False, min_value=1, max_value=32767, label="Xonalar")
    min_area = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=9,
        decimal_places=2,
        label="Maydon, dan (m²)",
    )
    max_area = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=9,
        decimal_places=2,
        label="Maydon, gacha (m²)",
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, label="Saralash")

    def __init__(self, *args, fixed_deal_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("min_price", "max_price", "min_area", "max_area"):
            self.fields[field_name].widget.attrs.update({"min": "0.01", "step": "0.01"})
        if fixed_deal_type:
            self.fields["deal_type"].disabled = True
            self.initial["deal_type"] = fixed_deal_type

    def clean(self):
        cleaned_data = super().clean()
        for minimum_name, maximum_name, label in (
            ("min_price", "max_price", "narx"),
            ("min_area", "max_area", "maydon"),
        ):
            minimum = cleaned_data.get(minimum_name)
            maximum = cleaned_data.get(maximum_name)
            if minimum is not None and maximum is not None and minimum > maximum:
                self.add_error(maximum_name, f"Maksimal {label} minimal qiymatdan kichik bo'lmasligi kerak.")
        return cleaned_data