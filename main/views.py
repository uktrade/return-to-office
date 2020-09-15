import datetime

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from notifications_python_client.notifications import NotificationsAPIClient

from .forms import BookingFormWhoFor, BookingFormInitial, BookingFormFinal
from .models import Booking, Floor, Building


def index(req):
    ctx = {}

    return render(req, "main/index.html", ctx)


def show_privacy_policy(req):
    ctx = {}

    return render(req, "main/show_privacy_policy.html", ctx)


def show_bookings(req):
    ctx = {}

    ctx["bookings"] = (
        Booking.objects.filter(
            user=req.user, is_active=True, booking_date__gte=datetime.date.today()
        )
        .order_by("booking_date")
        .select_related("building", "floor")
    )

    ctx["show_confirmation"] = req.GET.get("show_confirmation", False)
    ctx["show_cancellation"] = req.GET.get("show_cancellation", False)

    return render(req, "main/show_bookings.html", ctx)


def cancel_booking(req, pk):
    with transaction.atomic():
        b = get_object_or_404(Booking.objects.select_for_update(), pk=pk)
        failed = False

        if not b.is_active:
            messages.error(req, "Booking has already been cancelled")
            failed = True
        elif b.booking_date < datetime.date.today():
            messages.error(req, "Bookings in the past can not be cancelled")
            failed = True
        elif b.user != req.user:
            messages.error(req, "You can only cancel booking made by yourself")
            failed = True

        if failed:
            return redirect(reverse("main:show-bookings"))

        b.is_active = False
        b.canceled_timestamp = datetime.datetime.now()
        b.save()

        nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

        nc.send_email_notification(
            email_address=req.user.get_contact_email(),
            template_id="e07222ce-dbae-49c3-8e73-e2e52f2735b2",
            personalisation={
                "on_behalf_of": b.get_on_behalf_of(),
                "date": str(b.booking_date),
                "building": str(b.building),
                "floor": str(b.floor),
                "directorate": b.directorate,
            },
        )

        return redirect(reverse("main:show-bookings") + "?show_cancellation=1")


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
            req.session["on_behalf_of_name"] = form.cleaned_data["on_behalf_of_name"]
            req.session["on_behalf_of_dit_email"] = form.cleaned_data["on_behalf_of_dit_email"]

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
    on_behalf_of_name = req.session["on_behalf_of_name"]
    on_behalf_of_dit_email = req.session["on_behalf_of_dit_email"]

    if req.method == "POST":
        form = BookingFormFinal(req.POST)
        form.populate_floors(booking_date, building)

        if form.is_valid():
            booking = Booking(
                user=req.user,
                on_behalf_of_name=on_behalf_of_name or None,
                on_behalf_of_dit_email=on_behalf_of_dit_email or None,
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
                    lock_floors = Floor.objects.filter(  # noqa
                        pk=booking.floor_id
                    ).select_for_update()

                    bookings_cnt = Booking.objects.filter(
                        is_active=True,
                        booking_date=booking.booking_date,
                        building=booking.building,
                        floor=booking.floor,
                    ).count()

                    if bookings_cnt < booking.floor.nr_of_desks:
                        booking.save()

                        nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

                        nc.send_email_notification(
                            email_address=req.user.get_contact_email(),
                            template_id="15c64ab8-dba3-4ad5-a78a-cbec414f9603",
                            personalisation={
                                "on_behalf_of": booking.get_on_behalf_of(),
                                "date": str(booking.booking_date),
                                "building": str(booking.building),
                                "floor": str(booking.floor),
                                "directorate": booking.directorate,
                            },
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
    ctx["on_behalf_of_name"] = on_behalf_of_name
    ctx["on_behalf_of_dit_email"] = on_behalf_of_dit_email

    return render(req, "main/create_booking_finalize.html", ctx)
