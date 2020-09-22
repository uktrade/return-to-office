import datetime
import hmac

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from mohawk import Receiver
from mohawk.exc import CredentialsLookupError, MacMismatch, MissingAuthorization

from notifications_python_client.notifications import NotificationsAPIClient

from .forms import BookingFormWhoFor, BookingFormInitial, BookingFormFinal, BookingFormBusinessUnit
from .models import Booking, Floor, Building, DitGroup


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
            template_id="349eaf4a-c0d1-4e02-a263-6b85ee2557a9",
            personalisation={
                "on_behalf_of": b.get_on_behalf_of(),
                "date": str(b.booking_date),
                "building": str(b.building),
                "floor": str(b.floor),
                "dit_group": b.group or "Unknown",
                "business_unit": b.business_unit or "Unknown",
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
        if not req.GET.get("back", False):
            clear_booking_session_variables(req)
            initial = None
        else:
            initial = {"for_myself": str(int(req.session["for_myself"]))}

        form = BookingFormWhoFor(initial=initial)

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
            req.session["dit_group"] = int(form.cleaned_data["dit_group"])
            req.session["on_behalf_of_name"] = form.cleaned_data["on_behalf_of_name"]
            req.session["on_behalf_of_dit_email"] = form.cleaned_data["on_behalf_of_dit_email"]

            return redirect(reverse("main:booking-create-business-unit"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {
                "booking_date": req.session["booking_date"].isoformat(),
                "building": req.session["building"],
                "dit_group": req.session["dit_group"],
                "on_behalf_of_name": req.session["on_behalf_of_name"],
                "on_behalf_of_dit_email": req.session["on_behalf_of_dit_email"],
            }

        form = BookingFormInitial(for_myself, initial=initial)

    ctx["form"] = form
    ctx["for_myself"] = for_myself

    return render(req, "main/create_booking_initial.html", ctx)


def create_booking_business_unit(req):
    ctx = {}

    dit_group = req.session["dit_group"]

    if req.method == "POST":
        form = BookingFormBusinessUnit(dit_group, req.POST)

        if form.is_valid():
            req.session["business_unit"] = form.cleaned_data["business_unit"]

            return redirect(reverse("main:booking-create-finalize"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {
                "business_unit": req.session["business_unit"],
            }

        form = BookingFormBusinessUnit(dit_group, initial=initial)

    ctx["form"] = form

    return render(req, "main/create_booking_business_unit.html", ctx)


def create_booking_finalize(req):
    ctx = {}

    building = get_object_or_404(Building, pk=req.session["building"])
    booking_date = req.session["booking_date"]
    dit_group = get_object_or_404(DitGroup, pk=req.session["dit_group"]).name
    business_unit = req.session["business_unit"]
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
                group=dit_group,
                business_unit=business_unit,
            )

            if booking.booking_date < datetime.date.today():
                form.add_error(None, "Bookings cannot be in the past.")

            if booking.floor not in booking.building.floors.all():
                # this should not be possible, but guard against it anyway
                form.add_error(None, "Selected floor does not belong to the selected building.")

            if not form.errors:
                with transaction.atomic():
                    # lock the floor we're trying to book
                    locked_floor = Floor.objects.select_for_update().get(  # noqa
                        pk=booking.floor_id
                    )

                    bookings_cnt = Booking.objects.filter(
                        is_active=True,
                        booking_date=booking.booking_date,
                        building=booking.building,
                        floor=booking.floor,
                    ).count()

                    if bookings_cnt < booking.floor.nr_of_desks:
                        booking.save()
                        floor_has_space = True
                    else:
                        floor_has_space = False

                if floor_has_space:
                    nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

                    nc.send_email_notification(
                        email_address=req.user.get_contact_email(),
                        template_id="8df6e4a2-a29a-48f4-a03e-d00b9c5b3f49",
                        personalisation={
                            "on_behalf_of": booking.get_on_behalf_of(),
                            "date": str(booking.booking_date),
                            "building": str(booking.building),
                            "floor": str(booking.floor),
                            "dit_group": booking.group,
                            "business_unit": booking.business_unit,
                        },
                    )

                    clear_booking_session_variables(req)

                    return redirect(reverse("main:show-bookings") + "?show_confirmation=1")
                else:
                    form.add_error("floor", "Floor is completely booked")
    else:
        form = BookingFormFinal()
        form.populate_floors(booking_date, building)

    ctx["form"] = form
    ctx["booking_date"] = booking_date
    ctx["building"] = building
    ctx["dit_group"] = dit_group
    ctx["business_unit"] = business_unit
    ctx["on_behalf_of_name"] = on_behalf_of_name
    ctx["on_behalf_of_dit_email"] = on_behalf_of_dit_email

    return render(req, "main/create_booking_finalize.html", ctx)


def clear_booking_session_variables(req):
    """Clear booking flow related session variables."""

    for key in [
        "for_myself",
        "booking_date",
        "building",
        "dit_group",
        "business_unit",
        "on_behalf_of_name",
        "on_behalf_of_dit_email",
    ]:
        if key in req.session:
            req.session.delete(key)


def activity_stream_bookings(request):
    def lookup_credentials(passed_id):
        return (
            settings.ACTIVITY_STREAM_HAWK_CREDENTIALS
            if hmac.compare_digest(passed_id, settings.ACTIVITY_STREAM_HAWK_CREDENTIALS["id"])
            else None
        )

    try:
        Receiver(
            lookup_credentials,
            request.headers.get("Authorization"),
            request.build_absolute_uri(),
            request.method,
            content=request.body,
            content_type=request.headers.get("Content-Type"),
        )
    except (MissingAuthorization, CredentialsLookupError, MacMismatch):
        return JsonResponse(
            data={},
            status=403,
        )

    # Get cursor
    after_ts_str, after_booking_id_str = request.GET.get("cursor", "0.0_0").split("_")
    after_ts = datetime.datetime.fromtimestamp(float(after_ts_str))

    bookings = list(
        Booking.objects.extra(
            where=[
                "booked_timestamp > %s",
                "booked_timestamp < STATEMENT_TIMESTAMP() - INTERVAL '1 second'",
            ],
            params=(after_ts,),
        ).order_by("booked_timestamp")[: settings.ACTIVITY_STREAM_ITEMS_PER_PAGE]
    )

    abs_url = request.build_absolute_uri(reverse("main:activity-stream-bookings"))

    page = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
        ],
        "type": "Collection",
        "orderedItems": [
            {
                "id": f"dit:ReturnToOffice:Booking:{booking.id}:Update",
                "published": booking.booked_timestamp,
                "object": {
                    "id": f"dit:ReturnToOffice:Booking:{booking.id}",
                    "type": "dit:ReturnToOffice:Booking",
                    "dit:ReturnToOffice:Booking:userId": booking.user_id,
                    "dit:ReturnToOffice:Booking:userEmail": booking.user.email,
                    "dit:ReturnToOffice:Booking:userFullName": booking.user.get_short_name(),
                    "dit:ReturnToOffice:Booking:onBehalfOfName": booking.on_behalf_of_name,
                    "dit:ReturnToOffice:Booking:onBehalfOfEmail": booking.on_behalf_of_dit_email,
                    "dit:ReturnToOffice:Booking:bookingDate": booking.booking_date,
                    "dit:ReturnToOffice:Booking:building": booking.building.name,
                    "dit:ReturnToOffice:Booking:floor": booking.floor.name,
                    "dit:ReturnToOffice:Booking:directorate": booking.directorate,
                    "dit:ReturnToOffice:Booking:group": booking.group,
                    "dit:ReturnToOffice:Booking:businessUnit": booking.business_unit,
                    "dit:ReturnToOffice:Booking:created": booking.booked_timestamp,
                    "dit:ReturnToOffice:Booking:cancelled": booking.canceled_timestamp,
                },
            }
            for booking in bookings
        ],
        **(
            {
                "next": f"{abs_url}?cursor={bookings[-1].booked_timestamp.timestamp()}_{bookings[-1].id}"
            }
            if bookings
            else {}
        ),
    }

    return JsonResponse(
        data=page,
        status=200,
    )
