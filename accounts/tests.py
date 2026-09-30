from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from properties.models import Profile

User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-member",
                "email": "member@example.com",
                "first_name": "Ali",
                "last_name": "Valiyev",
                "password1": "long-and-secure-passphrase-934!",
                "password2": "long-and-secure-passphrase-934!",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="new-member")
        self.assertTrue(user.check_password("long-and-secure-passphrase-934!"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(username="existing", email="person@example.com")

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "another-member",
                "email": "PERSON@example.com",
                "password1": "long-and-secure-passphrase-934!",
                "password2": "long-and-secure-passphrase-934!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu email bilan hisob mavjud.")
        self.assertFalse(User.objects.filter(username="another-member").exists())


class AuthenticationAndProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="long-and-secure-passphrase-934!",
        )

    def test_auth_brand_links_to_homepage(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a class="brand" href="/" aria-label="UyTop bosh sahifasi">')

    def test_login_and_post_logout(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "member", "password": "long-and-secure-passphrase-934!"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))

    def test_logout_rejects_get_requests(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_profile_requires_login_and_updates_both_records(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Dilnoza",
                "last_name": "Karimova",
                "email": "updated@example.com",
                "phone": "+998901112233",
                "bio": "Uy izlayapman.",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Dilnoza")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.profile.phone, "+998901112233")
        self.assertEqual(self.user.profile.bio, "Uy izlayapman.")