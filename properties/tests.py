from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from properties.models import Favorite, Property


class PropertyModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="uytop-test")
        self.property_data = {
            "owner": self.user,
            "title": "Yangi kvartira, Toshkent",
            "description": "Yorug' va shinam xonadon.",
            "price": "125000.00",
            "deal_type": Property.DealType.SALE,
            "property_type": Property.PropertyType.APARTMENT,
            "city": "Toshkent",
            "district": "Chilonzor",
            "address": "Bunyodkor ko'chasi, 10",
            "area": "72.50",
            "renovation": Property.Renovation.GOOD,
            "phone": "+998901234567",
        }

    def test_slug_is_generated_and_collision_gets_suffix(self):
        first = Property.objects.create(**self.property_data)
        second = Property.objects.create(**self.property_data)

        self.assertEqual(first.slug, "yangi-kvartira-toshkent")
        self.assertEqual(second.slug, "yangi-kvartira-toshkent-2")
        self.assertEqual(first.status, Property.Status.PENDING)

    def test_user_cannot_favorite_same_property_twice(self):
        listing = Property.objects.create(**self.property_data)
        Favorite.objects.create(user=self.user, property=listing)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Favorite.objects.create(user=self.user, property=listing)


class PropertyAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="uytop-admin",
            email="admin@example.com",
            password="Secure-test-password-123",
        )
        self.owner = get_user_model().objects.create_user(username="listing-owner")
        self.listing = Property.objects.create(
            owner=self.owner,
            title="Admin tekshiruvi uchun uy",
            description="Sinov e'loni.",
            price="90000.00",
            deal_type=Property.DealType.SALE,
            property_type=Property.PropertyType.HOUSE,
            city="Samarqand",
            district="Markaz",
            address="Registon ko'chasi, 1",
            area="100.00",
            renovation=Property.Renovation.GOOD,
            phone="+998901234567",
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_approve_selected_property(self):
        response = self.client.post(
            reverse("admin:properties_property_changelist"),
            {
                "action": "approve_properties",
                "_selected_action": [str(self.listing.pk)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Property.Status.APPROVED)
        self.assertEqual(self.listing.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.listing.reviewed_at)
        self.assertEqual(self.listing.rejection_reason, "")

    def test_admin_can_reject_and_reset_moderation_audit(self):
        reject_response = self.client.post(
            reverse("admin:properties_property_changelist"),
            {
                "action": "reject_properties",
                "_selected_action": [str(self.listing.pk)],
            },
        )
        self.assertEqual(reject_response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Property.Status.REJECTED)
        self.assertEqual(self.listing.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.listing.reviewed_at)

        self.listing.rejection_reason = "Manzil ma'lumotini aniqlashtiring."
        self.listing.save(update_fields=["rejection_reason"])
        reset_response = self.client.post(
            reverse("admin:properties_property_changelist"),
            {
                "action": "reset_to_pending",
                "_selected_action": [str(self.listing.pk)],
            },
        )

        self.assertEqual(reset_response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Property.Status.PENDING)
        self.assertIsNone(self.listing.reviewed_by)
        self.assertIsNone(self.listing.reviewed_at)
        self.assertEqual(self.listing.rejection_reason, "")

    def test_property_change_page_includes_image_inline(self):
        response = self.client.get(
            reverse("admin:properties_property_change", args=[self.listing.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "images-TOTAL_FORMS")
        self.assertContains(response, "rejection_reason")


class HomePageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="home-owner")

    def create_property(self, **overrides):
        data = {
            "owner": self.user,
            "title": "Yorug' kvartira Chilonzorda",
            "description": "Yangi ta'mirlangan uy.",
            "price": "150000.00",
            "deal_type": Property.DealType.SALE,
            "property_type": Property.PropertyType.APARTMENT,
            "city": "Toshkent",
            "district": "Chilonzor",
            "address": "Bunyodkor ko'chasi, 12",
            "area": "74.00",
            "renovation": Property.Renovation.GOOD,
            "phone": "+998901234567",
            "status": Property.Status.APPROVED,
        }
        data.update(overrides)
        return Property.objects.create(**data)

    def test_home_shows_only_approved_and_featured_properties(self):
        featured = self.create_property(is_featured=True)
        self.create_property(title="Kutilayotgan e'lon", status=Property.Status.PENDING)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yorug")
        self.assertNotContains(response, "Kutilayotgan e'lon")
        self.assertEqual(list(response.context["featured_properties"]), [featured])

    def test_home_search_form_uses_the_property_list_route(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/properties/"')


class PropertyCrudTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="crud-owner",
            password="secure-test-password-123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-user",
            password="secure-test-password-123",
        )
        self.property_data = {
            "title": "Toshkentda hovli uy",
            "description": "Keng va yorug' hovli.",
            "deal_type": Property.DealType.SALE,
            "property_type": Property.PropertyType.HOUSE,
            "price": "2750000000.00",
            "city": "Toshkent",
            "district": "Yunusobod",
            "address": "Amir Temur ko'chasi, 20",
            "area": "180.00",
            "rooms": "5",
            "floor": "1",
            "total_floors": "2",
            "renovation": Property.Renovation.GOOD,
            "phone": "+998901234567",
        }

    def make_image(self, name):
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), color="steelblue").save(image_bytes, format="PNG")
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type="image/png")

    def create_listing(self, **overrides):
        data = {
            "owner": self.owner,
            **self.property_data,
            "status": Property.Status.PENDING,
        }
        data.update(overrides)
        return Property.objects.create(**data)

    def test_owner_can_create_listing_with_multiple_images(self):
        self.client.force_login(self.owner)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("properties:create"),
                {
                    **self.property_data,
                    "images": [self.make_image("front.png"), self.make_image("yard.png")],
                },
            )

            listing = Property.objects.get(owner=self.owner)
            self.assertRedirects(
                response,
                reverse("properties:detail", kwargs={"slug": listing.slug}),
            )
            self.assertEqual(listing.status, Property.Status.PENDING)
            self.assertEqual(listing.images.count(), 2)

    def test_create_and_edit_forms_render_for_owner(self):
        listing = self.create_listing()
        self.client.force_login(self.owner)

        create_response = self.client.get(reverse("properties:create"))
        edit_response = self.client.get(
            reverse("properties:edit", kwargs={"slug": listing.slug})
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "multiple")
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, listing.title)

    def test_non_image_upload_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("properties:create"),
            {
                **self.property_data,
                "images": SimpleUploadedFile(
                    "not-an-image.txt",
                    b"not an image",
                    content_type="text/plain",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rasm")
        self.assertFalse(Property.objects.filter(owner=self.owner).exists())

    def test_only_owner_or_staff_can_edit_or_delete(self):
        listing = self.create_listing()
        self.client.force_login(self.other_user)

        edit_response = self.client.get(
            reverse("properties:edit", kwargs={"slug": listing.slug})
        )
        delete_response = self.client.get(
            reverse("properties:delete", kwargs={"slug": listing.slug})
        )

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_owner_edit_resets_approved_listing_to_pending(self):
        listing = self.create_listing(
            status=Property.Status.APPROVED,
            reviewed_by=self.other_user,
            reviewed_at=timezone.now(),
        )
        listing.rejection_reason = "Old moderation note"
        listing.save(update_fields=["rejection_reason"])
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("properties:edit", kwargs={"slug": listing.slug}),
            {**self.property_data, "title": "Yangilangan uy e'loni"},
        )

        self.assertRedirects(
            response,
            reverse("properties:detail", kwargs={"slug": listing.slug}),
        )
        listing.refresh_from_db()
        self.assertEqual(listing.title, "Yangilangan uy e'loni")
        self.assertEqual(listing.status, Property.Status.PENDING)
        self.assertIsNone(listing.reviewed_by)
        self.assertIsNone(listing.reviewed_at)
        self.assertEqual(listing.rejection_reason, "")

    def test_owner_can_see_rejection_reason_on_private_detail(self):
        listing = self.create_listing(
            status=Property.Status.REJECTED,
            rejection_reason="Telefon raqamini tekshiring.",
        )
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("properties:detail", kwargs={"slug": listing.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Telefon raqamini tekshiring.")

    def test_unpublished_detail_is_private_to_owner_and_staff(self):
        listing = self.create_listing()
        detail_url = reverse("properties:detail", kwargs={"slug": listing.slug})

        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(detail_url).status_code, 200)
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

        listing.status = Property.Status.APPROVED
        listing.save()
        self.client.logout()
        self.assertEqual(self.client.get(detail_url).status_code, 200)

    def test_delete_requires_confirmation_and_post(self):
        listing = self.create_listing()
        self.client.force_login(self.owner)
        delete_url = reverse("properties:delete", kwargs={"slug": listing.slug})

        confirmation = self.client.get(delete_url)
        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(Property.objects.filter(pk=listing.pk).exists())

        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Property.objects.filter(pk=listing.pk).exists())


class PropertySearchTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="search-owner")

    def create_listing(self, title, **overrides):
        data = {
            "owner": self.owner,
            "title": title,
            "description": "Yorug' va shinam uy.",
            "price": "150000000.00",
            "deal_type": Property.DealType.SALE,
            "property_type": Property.PropertyType.APARTMENT,
            "city": "Toshkent",
            "district": "Chilonzor",
            "address": "Bunyodkor ko'chasi, 10",
            "area": "75.00",
            "rooms": 3,
            "renovation": Property.Renovation.GOOD,
            "phone": "+998901234567",
            "status": Property.Status.APPROVED,
        }
        data.update(overrides)
        return Property.objects.create(**data)

    def test_all_search_filters_can_be_combined(self):
        matching = self.create_listing("Yorug' kvartira")
        self.create_listing(
            "Samarqanddagi uy",
            city="Samarqand",
            district="Markaz",
            deal_type=Property.DealType.RENT,
        )
        self.create_listing("Qimmat kvartira", price="250000000.00")

        response = self.client.get(
            reverse("properties:list"),
            {
                "q": "yorug'",
                "deal_type": "sale",
                "property_type": "apartment",
                "city": "toshkent",
                "district": "chilonzor",
                "min_price": "100000000",
                "max_price": "200000000",
                "rooms": "3",
                "min_area": "70",
                "max_area": "90",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result_count"], 1)
        self.assertEqual(list(response.context["page_obj"].object_list), [matching])

    def test_sale_and_rent_routes_enforce_deal_type(self):
        sale = self.create_listing("Sotuvdagi uy")
        self.create_listing("Ijara uyi", deal_type=Property.DealType.RENT)
        self.create_listing("Kutilayotgan uy", status=Property.Status.PENDING)

        sale_response = self.client.get(
            reverse("properties:sale"),
            {"deal_type": "rent"},
        )
        rent_response = self.client.get(reverse("properties:rent"))

        self.assertEqual(list(sale_response.context["page_obj"].object_list), [sale])
        self.assertEqual(sale_response.context["result_count"], 1)
        self.assertEqual(rent_response.context["result_count"], 1)
        self.assertTrue(
            all(item.status == Property.Status.APPROVED for item in rent_response.context["page_obj"])
        )

    def test_sorting_and_pagination_preserve_search_parameters(self):
        listings = [
            self.create_listing(f"Uy {index}", price=f"{100000000 + index * 1000000}.00")
            for index in range(14)
        ]

        response = self.client.get(
            reverse("properties:list"),
            {"sort": "price_asc", "city": "Toshkent", "page": "2"},
        )
        page = response.context["page_obj"]

        self.assertEqual(page.number, 2)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(list(page.object_list), listings[12:])
        self.assertEqual(response.context["sort_label"], "Narx: arzonidan")
        self.assertIn("city=Toshkent", response.context["pagination_query"])
        self.assertNotIn("page=", response.context["pagination_query"])

    def test_invalid_range_returns_form_error_without_unfiltered_results(self):
        self.create_listing("Mavjud uy")

        response = self.client.get(
            reverse("properties:list"),
            {"min_price": "200000000", "max_price": "100000000"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(response.context["result_count"], 0)

    def test_search_hides_unapproved_listings(self):
        self.create_listing("Yopiq uy", status=Property.Status.REJECTED)

        response = self.client.get(reverse("properties:list"))

        self.assertEqual(response.context["result_count"], 0)