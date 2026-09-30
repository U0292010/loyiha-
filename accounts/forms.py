from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from properties.models import Profile

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")
        labels = {
            "username": "Foydalanuvchi nomi",
            "first_name": "Ism",
            "last_name": "Familiya",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email bilan hisob mavjud.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["password1"].label = "Parol"
        self.fields["password2"].label = "Parolni tasdiqlang"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"


class UyTopAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Foydalanuvchi nomi"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password"].label = "Parol"
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"


class AccountUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Ism", "last_name": "Familiya"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        existing = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("Bu email boshqa hisobda ishlatilmoqda.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "bio", "avatar")
        labels = {
            "phone": "Telefon raqami",
            "bio": "O'zingiz haqingizda",
            "avatar": "Profil rasmi",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"autocomplete": "tel"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }