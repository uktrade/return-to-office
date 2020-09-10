import datetime

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse

from notifications_python_client.notifications import NotificationsAPIClient

from .forms import BookingFormWhoFor, BookingFormInitial, BookingFormFinal
from .models import Booking, Floor, Building


def index(req):
    ctx = {}

    return render(req, "main/index.html", ctx)


def show_bookings(req):
    ctx = {}

    ctx["bookings"] = Booking.objects.filter(
        user=req.user, booking_date__gte=datetime.date.today()
    ).order_by("booking_date"
    ).select_related("building", "floor")

    ctx["show_confirmation"] = req.GET.get("show_confirmation", False)

    return render(req, "main/show_bookings.html", ctx)


def create_booking_who_for(req):
    ctx = {}

    if req.method == "POST":
        form = BookingFormWhoFor(req.POST)

        if form.is_valid():
            req.session["for_myself"] = bool(int(form.cleaned_data["for_myself"]))

            return redirect(reverse("main:booking-create-initial"))
    else:
        form = BookingFormWhoFor()

    ctx["form"] = form

    return render(req, "main/create_booking_who_for.html", ctx)



def create_booking_initial(req):
    ctx = {}

    for_myself = req.session["for_myself"]

    if req.method == "POST":
        form = BookingFormInitial(for_myself, req.POST)

        if form.is_valid():
            req.session["booking_date"] = form.cleaned_data["booking_date"]
            req.session["building"] = int(form.cleaned_data["building"])
            req.session["directorate"] = form.cleaned_data["directorate"]
            req.session["on_behalf_of"] = form.cleaned_data["on_behalf_of"]

            return redirect(reverse("main:booking-create-finalize"))
    else:
        form = BookingFormInitial(for_myself)

    ctx["form"] = form
    ctx["for_myself"] = for_myself

    return render(req, "main/create_booking_initial.html", ctx)


def create_booking_finalize(req):
    ctx = {}

    building = get_object_or_404(Building, pk=req.session["building"])
    booking_date = req.session["booking_date"]
    directorate = req.session["directorate"]
    on_behalf_of = req.session["on_behalf_of"]

    if req.method == "POST":
        form = BookingFormFinal(req.POST)
        form.populate_floors(booking_date, building)

        if form.is_valid():
            booking = Booking(
                user=req.user,
                on_behalf_of_name=on_behalf_of or None,
                building=building,
                booking_date=booking_date,
                floor=get_object_or_404(Floor, pk=int(form.cleaned_data["floor"])),
                directorate=directorate,
            )

            if booking.booking_date < datetime.date.today():
                form.add_error(None, "Bookings cannot be in the past.")

            if booking.floor not in booking.building.floors.all():
                # this should not be possible, but guard against it anyway
                form.add_error(None, "Selected floor does not belong to the selected building.")

            if not form.errors:
                with transaction.atomic():
                    # lock the floor we're trying to book
                    lock_floors = Floor.objects.filter(pk=booking.floor_id).select_for_update()

                    bookings_cnt = Booking.objects.filter(
                        booking_date=booking.booking_date, building=booking.building, floor=booking.floor
                    ).count()

                    if bookings_cnt < booking.floor.nr_of_desks:
                        booking.save()

                        notifications_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

                        notifications_client.send_email_notification(
                            email_address=req.user.email,
                            template_id="15c64ab8-dba3-4ad5-a78a-cbec414f9603",
                            personalisation={
                                "on_behalf_of": booking.on_behalf_of_name if booking.on_behalf_of_name else "Yourself",
                                "date": str(booking.booking_date),
                                "building": str(booking.building),
                                "floor": str(booking.floor),
                                "directorate": booking.directorate,
                            }
                        )

                        # TODO: clear booking data from session?

                        return redirect(reverse("main:show-bookings") + "?show_confirmation=1")
                    else:
                        form.add_error("floor", "Floor is completely booked")
    else:
        form = BookingFormFinal()
        form.populate_floors(booking_date, building)

    ctx["form"] = form
    ctx["booking_date"] = booking_date
    ctx["building"] = building
    ctx["directorate"] = directorate
    ctx["on_behalf_of"] = on_behalf_of

    return render(req, "main/create_booking_finalize.html", ctx)
