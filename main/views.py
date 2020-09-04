import datetime
from typing import NamedTuple

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import BookingFormInitial, BookingFormFinal
from .models import Booking, Floor, Building


class FloorBookingInfo(NamedTuple):
    floor_name: str
    total_desks: int
    free_desks: int


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
    template = "main/create_booking_initial.html"

    ctx = {}

    if req.method == "POST":
        form = BookingFormInitial(req.POST)

        if form.is_valid():
            booking = form.save(False)

            form = BookingFormFinal(
                building=booking.building,
                initial={
                    "booking_date": booking.booking_date,
                    "building": booking.building,
                }
            )

            template = "main/create_booking_finalize.html"

            floors = Floor.objects.filter(building=booking.building)

            all_bookings = Booking.objects.filter(
                booking_date=booking.booking_date, building=booking.building)

            # key = floor name, value = [number of bookings, total desks]
            bookings_per_floor = {f.name: [0, f.nr_of_desks()] for f in floors}

            for b in all_bookings:
                bookings_per_floor[b.floor.name][0] += 1

            floor_booking_info = []

            for floor_name in sorted(bookings_per_floor.keys()):
                val = bookings_per_floor[floor_name]

                floor_booking_info.append(FloorBookingInfo(
                    floor_name=floor_name,
                    free_desks=val[1] - val[0],
                    total_desks=val[1],
                ))

            ctx["floor_booking_info"] = floor_booking_info
            ctx["booking_date"] = booking.booking_date
            ctx["building"] = booking.building

    else:
        form = BookingFormInitial()

    ctx["form"] = form

    return render(req, template, ctx)


@require_POST
def create_booking_finalize(req):
    form = BookingFormFinal(req.POST)

    if form.is_valid():
        booking = form.save(False)
        booking.user = req.user

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

    # FIXME: in theory, this should do all the things create_booking_initial
    # does..not sure how this would ever go here in practise though
    ctx = {}
    ctx["form"] = form

    return render(req, "main/create_booking_finalize.html", ctx)
