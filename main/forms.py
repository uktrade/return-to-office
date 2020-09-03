import datetime

from django import forms

from .models import Booking, Floor

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "building"]

        widgets = {
            "booking_date": forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        if booking_date < datetime.date.today():
            raise forms.ValidationError("Bookings cannot be in the past.")

        return booking_date


class BookingForm2(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "building", "floor"]

        widgets = {
            "booking_date": forms.HiddenInput(),
            "building": forms.HiddenInput(),
        }

    def __init__(self, *args, building=None, **kwargs):
        super().__init__(*args, **kwargs)

        if building:
            self.fields['floor'].queryset = Floor.objects.filter(building=building).order_by("name")

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        if booking_date < datetime.date.today():
            raise forms.ValidationError("Bookings cannot be in the past.")

        return booking_date
