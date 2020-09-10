import datetime

from django import forms
from django.utils.safestring import mark_safe
from django.core.validators import validate_email

from .models import Booking, Floor, Building
from .widgets import GovUKCheckboxInput, GovUKRadioSelect, GovUKTextInput


class BookingFormWhoFor(forms.Form):
    for_myself = forms.ChoiceField(label="Who are you booking for?", widget=GovUKRadioSelect(), choices=[
        ("1", "Myself"),
        ("0", "Someone else"),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["for_myself"].widget.form_instance = self


class BookingFormInitial(forms.Form):
    on_behalf_of_name = forms.CharField(
        required=False, widget=GovUKTextInput(), label="On behalf of",
        help_text="If booking on behalf of a visitor, please enter their name",
    )

    on_behalf_of_dit_email = forms.CharField(
        required=False, widget=GovUKTextInput(), label="On behalf of",
        help_text="Or if booking on behalf of DIT staff, please enter their email address",
    )

    booking_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    building = forms.ChoiceField(label="Building", widget=GovUKRadioSelect())
    directorate = forms.ChoiceField(label="Directorate", widget=GovUKRadioSelect())

    def __init__(self, for_myself, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.for_myself = for_myself

        self.fields["building"].widget.form_instance = self
        self.fields["directorate"].widget.form_instance = self
        self.fields["on_behalf_of_name"].widget.form_instance = self
        self.fields["on_behalf_of_dit_email"].widget.form_instance = self

        self.fields['booking_date'].widget.attrs.update({
            "min": str(datetime.date.today()),
        })

        self.fields["building"].choices = [(b.pk, str(b)) for b in Building.objects.all().order_by("name")]

        self.fields["directorate"].choices = [(x, x) for x in [
            "Communications and Marketing",
            "Corporate Services",
            "GREAT",
            "GTI",
            "Strategy",
            "TPG",
            "TRID",
            "UKEF",
            "External",
        ]]

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        if booking_date < datetime.date.today():
            raise forms.ValidationError("Bookings cannot be in the past.")

        return booking_date

    def clean(self):
        if not self.for_myself:
            name =  self.cleaned_data.get("on_behalf_of_name")
            dit_email = self.cleaned_data.get("on_behalf_of_dit_email")

            if not any(bool(x.strip()) if x else False for x in [name, dit_email]):
                self.add_error(None, forms.ValidationError("One of the 'on behalf of' fields must be filled"))

            if dit_email:
                try:
                    validate_email(dit_email)
                except forms.ValidationError:
                    self.add_error("on_behalf_of_dit_email", forms.ValidationError("If not empty, this must be a valid email address"))


class BookingFormFinal(forms.Form):
    floor = forms.ChoiceField(label="Floor", widget=GovUKRadioSelect())

    confirmation = forms.BooleanField(label=mark_safe("""
    <p class="govuk-body">By making a booking I confirm that I, or the person on whose behalf I am making the booking have:</p>

    <ul class="govuk-list govuk-list--bullet">
    <li>Completed a Personal Risk Assessment after consultation with my/their line manager
    <li>Agreed with my/their line manager that it is safe to attend the office subject to any mitigation measures needed
    <li>Have the agreement of a member of the SCS in my line management chain to return to the office
    <li>Viewed the presentation on the 'Returning to DIT offices' digital workspace page
    <li>If booking a desk in the secure area,  I, or the person on whose behalf I am making the booking, hold the appropriate level of access required to use this area
    <li>Will not attend the office if I/they or any member of my/their household have symptoms of Covid-19; or
    <li>In a case where I am booking for a visitor – I have or will send them annex 1 of the building user guide before they attend the office
    </ul>"""), widget=GovUKCheckboxInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["floor"].widget.form_instance = self
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
            (f.pk, f"{f.name}: {f.nr_of_desks - f.nr_of_bookings} free desks out of the {f.nr_of_desks} total desks")
            for f in floors.values()
        ]
