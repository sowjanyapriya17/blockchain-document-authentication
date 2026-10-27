
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Profile


class SignupForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    role = forms.ChoiceField(
        choices=[
            ('ISSUER', 'Issuer'),
            ('VERIFIER', 'Verifier'),
        ],
        label="Register As"
    )

    class Meta:
        model = User

        fields = [
            'username',
            'email',
            'password',
        ]

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

