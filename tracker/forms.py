from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .choices import Roles
from .models import CustomUser


class SignUpForm(forms.ModelForm):
    """
    A form for user sign-up that extends Django's ModelForm.

    This form is built on the CustomUser model and includes email, password, and confirm_password fields.
    It ensures that the password and confirm_password match during validation.

    Attributes:
        email (EmailField): An email input field for the user's email.
        password (CharField): A password input field for the user's password.
        confirm_password (CharField): A password input field to confirm the user's password.
        role (ChoiceField): A dropdown of user roles (contributor, tech-lead).

    Meta:
        model (CustomUser): The model that this form is built on.
        fields (list): A list of fields to include in the form, in this case, 'email' and 'password'.

    Methods:
        clean() -> dict:
            Validates the form data ensuring that the password and confirm_password are identical.
    """

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    role = forms.ChoiceField(choices=Roles.choices)

    class Meta:
        model = CustomUser
        fields = ("email", "password")

    def clean(self) -> dict:
        """
        Validates if passwords match.
        :return: cleaned_data
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit: bool = True) -> CustomUser:
        """
        Creates a new superuser.
        :param commit: bool
        :return: CustomUser
        """
        with transaction.atomic():
            new_user = CustomUser.objects.create_superuser(
                email=self.cleaned_data.get("email", ""),
                password=self.cleaned_data.get("password", ""),
                role=self.cleaned_data.get("role", ""),
            )

            return new_user
