from django import forms
from django.contrib.auth.models import User
from core.models import Establishment
from .models import Reservation, PositiveReport


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    captcha = forms.CharField(max_length=100)
    is_manager = forms.BooleanField(required=False, label="I'm a manager")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

class EstablishmentForm(forms.ModelForm):
    class Meta:
        model = Establishment
        fields = ["name", "capacity", "is_compliant"]

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["establishment", "date", "nb_people"]
        # Give the date field a proper calendar picker in the browser.
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean_date(self):
        from django.utils import timezone
        d = self.cleaned_data["date"]
        if d < timezone.now().date():
            raise forms.ValidationError("Cannot reserve a past date.")
        return d

class PositiveReportForm(forms.ModelForm):
    class Meta:
        model = PositiveReport
        fields = ["test_date"]
        widgets = {"test_date": forms.DateInput(attrs={"type": "date"})}