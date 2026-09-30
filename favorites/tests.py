from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from properties.models import Favorite, Property


class FavoriteTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="favorite-user")
        self.other_user = user_model.objects.create_user(username="other-favorite-user")
        self.listing = Property.objects.create(
            owner=self.other_user,
            title="Saqlanadigan xonadon",
            description="Tasdiqlangan e'lon.",
            price="150000000.00",
            deal_type=Property.DealType.SALE,
            property_type=Property.PropertyType.APARTMENT,
            city="Toshkent",
            district="Yunusobod",
            address="Amir Temur ko'chasi, 3",
            area="78.00",
            rooms=3,
            renovation=Property.Renovation.GOOD,
            phone="+998901234567",
            status=Property.Status.APPROVED,
        )

    def test_authenticated_post_toggles_favorite(self):
        self.client.force_login(self.user)
        toggle_url = reverse("favorites:toggle", kwargs={"slug": self.listing.slug})

        added = self.client.post(toggle_url, {"next": reverse("properties:list")})
        self.assertRedirects(added, reverse("properties:list"))
        self.assertTrue(Favorite.objects.filter(user=self.user, property=self.listing).exists())

        removed = self.client.post(toggle_url, {"next": reverse("properties:list")})
        self.assertRedirects(removed, reverse("properties:list"))
        self.assertFalse(Favorite.objects.filter(user=self.user, property=self.listing).exists())

    def test_anonymous_toggle_redirects_to_login(self):
        response = self.client.post(
            reverse("favorites:toggle", kwargs={"slug": self.listing.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertFalse(Favorite.objects.exists())

    def test_toggle_rejects_get_and_unapproved_properties(self):
        toggle_url = reverse("favorites:toggle", kwargs={"slug": self.listing.slug})
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(toggle_url).status_code, 405)

        self.listing.status = Property.Status.PENDING
        self.listing.save()
        self.assertEqual(self.client.post(toggle_url).status_code, 404)
        self.assertFalse(Favorite.objects.exists())

    def test_external_next_url_falls_back_to_favorites_page(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("favorites:toggle", kwargs={"slug": self.listing.slug}),
            {"next": "https://example.invalid/"},
        )

        self.assertRedirects(response, reverse("favorites:list"))

    def test_favorites_page_shows_only_current_users_approved_properties(self):
        saved = Favorite.objects.create(user=self.user, property=self.listing)
        other_listing = Property.objects.create(
            owner=self.other_user,
            title="Boshqa saqlangan uy",
            description="Boshqa foydalanuvchiga tegishli favorite.",
            price="120000000.00",
            deal_type=Property.DealType.RENT,
            property_type=Property.PropertyType.HOUSE,
            city="Samarqand",
            district="Markaz",
            address="Registon ko'chasi, 9",
            area="110.00",
            renovation=Property.Renovation.GOOD,
            phone="+998901234567",
            status=Property.Status.APPROVED,
        )
        Favorite.objects.create(user=self.other_user, property=other_listing)
        hidden_listing = Property.objects.create(
            owner=self.other_user,
            title="Rad etilgan uy",
            description="Moderatsiyadan o'tmagan.",
            price="90000000.00",
            deal_type=Property.DealType.SALE,
            property_type=Property.PropertyType.HOUSE,
            city="Buxoro",
            district="Markaz",
            address="Eski shahar, 1",
            area="90.00",
            renovation=Property.Renovation.NEEDS_REPAIR,
            phone="+998901234567",
            status=Property.Status.REJECTED,
        )
        Favorite.objects.create(user=self.user, property=hidden_listing)
        self.client.force_login(self.user)

        response = self.client.get(reverse("favorites:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["properties"]), [saved.property])
        self.assertContains(response, self.listing.title)
        self.assertContains(response, 'aria-pressed="true"')
        self.assertNotContains(response, other_listing.title)
        self.assertNotContains(response, hidden_listing.title)

    def test_saved_state_is_rendered_on_home_and_detail_pages(self):
        Favorite.objects.create(user=self.user, property=self.listing)
        self.client.force_login(self.user)

        home_response = self.client.get(reverse("home"))
        detail_response = self.client.get(
            reverse("properties:detail", kwargs={"slug": self.listing.slug})
        )

        self.assertContains(home_response, 'aria-pressed="true"')
        self.assertContains(detail_response, 'aria-pressed="true"')

    def test_favorites_page_requires_login(self):
        response = self.client.get(reverse("favorites:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)