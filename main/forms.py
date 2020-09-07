import datetime

from django import forms
from django.utils.safestring import mark_safe

from .models import Booking, Floor, Building
from .widgets import GovUKCheckboxInput


class BookingFormInitial(forms.Form):
    booking_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    building = forms.ChoiceField(widget=forms.RadioSelect())
    directorate = forms.ChoiceField(widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['booking_date'].widget.attrs.update({
            "min": str(datetime.date.today()),
        })

        self.fields["building"].choices = [(b.pk, str(b)) for b in Building.objects.all().order_by("name")]

        self.fields["directorate"].choices = [(x, x) for x in [
            "Chief Operating Officer",
            "Ministerial Strategy Directorate",
            "Global Trade and Investment",
            "Trade Policy Group",
            "Global Strategy Directorate",
            "Other / Visitor",
        ]]

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        if booking_date < datetime.date.today():
            raise forms.ValidationError("Bookings cannot be in the past.")

        return booking_date


class BookingFormFinal(forms.Form):
    floor = forms.ChoiceField(widget=forms.RadioSelect())

    confirmation = forms.BooleanField(label=mark_safe("""
    <p class="govuk-body">By making a booking I confirm that I, or the person on whose behalf I am making the booking have:</p>

    <ul class="govuk-list govuk-list--bullet">
    <li>Completed a Personal Risk Assessment after consultation with my/their line manager
    <li>Agreed with my/their line manager that it is safe to attend the office subject to any mitigation measures needed
    <li>Viewed the presentation on the 'Returning to DIT offices' digital workspace page
    <li>Will not attend the office if I/they or any member of my/their household have symptoms of Covid-19; or
    <li>In a case where I am booking for a visitor – I have or will send them annex 1 of the building user guide before they attend the office
    </ul>"""), widget=GovUKCheckboxInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["confirmation"].widget.form_instance = self

    def populate_floors(self, booking_date: datetime.date, building: Building) -> None:
        # key = floor id, value = Floor
        floors = {f.pk: f for f in Floor.objects.filter(building=building).order_by("name")}

        for f in floors.values():
            f.nr_of_bookings = 0

        all_bookings = Booking.objects.filter(booking_date=booking_date, building=building)

        for b in all_bookings:
            floors[b.floor.pk].nr_of_bookings += 1

        self.fields["floor"].choices = [
            (f.pk, f"{f.name}: {f.nr_of_desks() - f.nr_of_bookings} free desks out of the {f.nr_of_desks()} total desks")
            for f in floors.values()
        ]
