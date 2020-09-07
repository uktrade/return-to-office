import datetime

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse

from .forms import BookingFormInitial, BookingFormFinal
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

    return render(req, "main/show_bookings.html", ctx)


def create_booking_initial(req):
    ctx = {}

    if req.method == "POST":
        form = BookingFormInitial(req.POST)

        if form.is_valid():
            req.session["booking_date"] = form.cleaned_data["booking_date"]
            req.session["building"] = int(form.cleaned_data["building"])
            req.session["directorate"] = form.cleaned_data["directorate"]

            return redirect(reverse("main:booking-create-finalize"))
    else:
        form = BookingFormInitial()

    ctx["form"] = form

    return render(req, "main/create_booking_initial.html", ctx)


def create_booking_finalize(req):
    ctx = {}

    building = get_object_or_404(Building, pk=req.session["building"])
    booking_date = req.session["booking_date"]
    directorate = req.session["directorate"]

    if req.method == "POST":
        form = BookingFormFinal(req.POST)
        form.populate_floors(booking_date, building)

        if form.is_valid():
            booking = Booking(
                user=req.user,
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

                    all_bookings = Booking.objects.filter(
                        booking_date=booking.booking_date, building=booking.building, floor=booking.floor
                    )

                    if len(all_bookings) >= booking.floor.nr_of_desks():
                        messages.error(req, "Floor is completely booked")

                        return redirect("main:index")

                    booking.desk = booking.floor.get_free_desk(set(b.desk for b in all_bookings))
                    booking.save()

                    messages.success(req, "Desk booking successfully completed")

                    # FIXME: send email confirmation

                    return redirect("main:show-bookings")
    else:
        form = BookingFormFinal()
        form.populate_floors(booking_date, building)

    ctx["form"] = form
    ctx["booking_date"] = booking_date
    ctx["building"] = building
    ctx["directorate"] = directorate

    return render(req, "main/create_booking_finalize.html", ctx)
