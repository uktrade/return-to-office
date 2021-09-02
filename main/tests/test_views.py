import os
from datetime import datetime

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from freezegun import freeze_time
from mohawk import Sender

from main.tests import factories
from main.tests.utils import create_test_user


def expected_booking_data(booking):
    return {
        "id": f"dit:ReturnToOffice:Booking:{booking.id}:Update",
        "published": booking.booked_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "object": {
            "id": f"dit:ReturnToOffice:Booking:{booking.id}",
            "type": "dit:ReturnToOffice:Booking",
            "dit:ReturnToOffice:Booking:bookingId": booking.id,
            "dit:ReturnToOffice:Booking:userId": booking.user.id,
            "dit:ReturnToOffice:Booking:userEmail": booking.user.email,
            "dit:ReturnToOffice:Booking:userFullName": f"{booking.user.first_name} {booking.user.last_name}",
            "dit:ReturnToOffice:Booking:onBehalfOfName": booking.on_behalf_of_name,
            "dit:ReturnToOffice:Booking:onBehalfOfEmail": booking.on_behalf_of_dit_email,
            "dit:ReturnToOffice:Booking:bookingDate": str(booking.booking_date.date()),
            "dit:ReturnToOffice:Booking:building": booking.building.name,
            "dit:ReturnToOffice:Booking:floor": booking.floor.name,
            "dit:ReturnToOffice:Booking:directorate": booking.directorate,
            "dit:ReturnToOffice:Booking:group": booking.group,
            "dit:ReturnToOffice:Booking:businessUnit": booking.business_unit,
            "dit:ReturnToOffice:Booking:created": booking.booked_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "dit:ReturnToOffice:Booking:cancelled": booking.canceled_timestamp,
        },
    }


class TestNoSessionViewing(TestCase):
    def setUp(self):
        self.create_pra_business_unit_url = reverse("main:pra-create-business-unit")

    def test_user_without_pra_session_is_redirected(self):
        test_user = create_test_user()
        self.client.force_login(test_user)

        response = self.client.get(
            self.create_pra_business_unit_url,
        )
        self.assertEqual(response.status_code, 302)

    def test_user_with_pra_session_is_not_redirected(self):
        test_user = create_test_user()
        self.client.force_login(test_user)

        session = self.client.session
        session["pra_dit_group"] = 1
        session.save()

        response = self.client.get(
            self.create_pra_business_unit_url,
        )
        self.assertEqual(response.status_code, 200)


class TestActivityStreamView(TestCase):
    def setUp(self):
        self.url = f"http://testserver{reverse('main:activity-stream-bookings')}"

    def test_no_header_provided(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated(self):
        sender = Sender(
            {
                "id": os.environ["ACTIVITY_STREAM_HAWK_ID"],
                "key": "incorrect-key",
                "algorithm": "sha256",
            },
            self.url,
            "GET",
            content="",
            content_type="",
        )

        response = self.client.get(
            self.url,
            extra={
                "Authorization": sender.request_header,
                "Content-Type": "",
            },
        )
        self.assertEqual(response.status_code, 403)

    @freeze_time("2020-09-01 02:00:00")
    @override_settings(ACTIVITY_STREAM_ITEMS_PER_PAGE=1)
    def test_authenticated(self):
        booking1 = factories.BookingFactory(
            booking_date=datetime(2020, 9, 1),
        )
        booking1.booked_timestamp = datetime(2020, 8, 30)
        booking1.save()
        booking2 = factories.BookingFactory(
            booking_date=datetime(2020, 9, 2),
        )
        booking2.booked_timestamp = datetime(2020, 8, 31)
        booking2.save()
        sender = Sender(
            settings.ACTIVITY_STREAM_HAWK_CREDENTIALS, self.url, "GET", content="", content_type=""
        )

        # Page 1
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_CONTENT_TYPE="",
        )
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertEqual(
            json_response,
            {
                "@context": [
                    "https://www.w3.org/ns/activitystreams",
                    {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
                ],
                "type": "Collection",
                "orderedItems": [expected_booking_data(booking1)],
                "next": f"{self.url}?cursor={booking1.booked_timestamp.timestamp()}_{booking1.id}",
            },
        )

        # Page 2
        sender = Sender(
            settings.ACTIVITY_STREAM_HAWK_CREDENTIALS,
            json_response["next"],
            "GET",
            content="",
            content_type="",
        )
        response = self.client.get(
            json_response["next"],
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_CONTENT_TYPE="",
        )
        json_response = response.json()
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            json_response,
            {
                "@context": [
                    "https://www.w3.org/ns/activitystreams",
                    {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
                ],
                "type": "Collection",
                "orderedItems": [expected_booking_data(booking2)],
                "next": f"{self.url}?cursor={booking2.booked_timestamp.timestamp()}_{booking2.id}",
            },
        )

        # Page 3 (empty)
        sender = Sender(
            settings.ACTIVITY_STREAM_HAWK_CREDENTIALS,
            json_response["next"],
            "GET",
            content="",
            content_type="",
        )
        response = self.client.get(
            json_response["next"],
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_CONTENT_TYPE="",
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "@context": [
                    "https://www.w3.org/ns/activitystreams",
                    {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
                ],
                "type": "Collection",
                "orderedItems": [],
            },
        )
