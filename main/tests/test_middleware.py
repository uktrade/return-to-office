from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from main.middleware import IpRestrictionMiddleware


def dummy_view(_):
    return HttpResponse(status=200)


class TestIpRestrictionMiddleware(TestCase):

    rf = None

    def setUp(self):
        self.rf = RequestFactory()

    def test_middleware_is_enabled(self):
        with self.settings(IP_RESTRICT=True, IP_RESTRICT_APPS=["admin"]):
            self.assertEqual(self.client.get(reverse("admin:index")).status_code, 401)

    def test_applies_to_specified_apps_only(self):
        """Only apps listed in `settings.IP_WHITELIST_APPS` should be ip restricted"""

        request = self.rf.get("/")

        with self.settings(IP_RESTRICT=True, IP_RESTRICT_APPS=["admin"]):
            self.assertEqual(IpRestrictionMiddleware(dummy_view)(request).status_code, 200)

    def test_not_enabled_if_ip_restrict_is_false(self):

        request = self.rf.get(reverse("admin:index"), HTTP_X_FORWARDED_FOR="")

        with self.settings(IP_RESTRICT=False, IP_RESTRICT_APPS=["admin"]):
            self.assertEqual(IpRestrictionMiddleware(dummy_view)(request).status_code, 200)

    def test_x_forwarded_header(self):

        test_cases = (["1.1.1.1, 2.2.2.2, 3.3.3.3", 200], ["1.1.1.1", 401], ["", 401])

        for xff_header, expected_status in test_cases:
            request = self.rf.get(reverse("admin:index"), HTTP_X_FORWARDED_FOR=xff_header)

            with self.settings(
                IP_RESTRICT=True, IP_RESTRICT_APPS=["admin"], ALLOWED_IPS=["2.2.2.2"]
            ):
                self.assertEqual(
                    IpRestrictionMiddleware(dummy_view)(request).status_code,
                    expected_status,
                )

    def test_ips(self):

        test_cases = ([["2.2.2.2"], 200], [["1.1.1.1"], 401])

        for allowed_ips, expected_status in test_cases:
            with self.settings(
                IP_RESTRICT=True, IP_RESTRICT_APPS=["admin"], ALLOWED_IPS=allowed_ips
            ):
                request = self.rf.get(
                    reverse("admin:index"),
                    HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2, 3.3.3.3",
                )

                self.assertEqual(
                    IpRestrictionMiddleware(dummy_view)(request).status_code,
                    expected_status,
                )

        with self.settings(IP_RESTRICT=True, IP_RESTRICT_APPS=["admin"], ALLOWED_IPS=["3.3.3.3"]):

            self.assertEqual(IpRestrictionMiddleware(dummy_view)(request).status_code, 401)

    def test_ip_restricted_path(self):

        test_cases = ([["2.2.2.2"], 200], [["1.1.1.1"], 401])

        for allowed_ips, expected_status in test_cases:
            with self.settings(
                IP_RESTRICT=True,
                IP_RESTRICT_PATH_NAMES=["main:show-bookings"],
                ALLOWED_IPS=allowed_ips,
            ):
                request = self.rf.get(
                    reverse("main:show-bookings"),
                    HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2, 3.3.3.3",
                )

                self.assertEqual(
                    IpRestrictionMiddleware(dummy_view)(request).status_code,
                    expected_status,
                )
