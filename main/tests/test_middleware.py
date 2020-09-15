import pytest
from django.http import HttpResponse
from django.urls import reverse

from main.middleware import IpRestrictionMiddleware


def dummy_view(_):
    return HttpResponse(status=200)


class TestIpRestrictionMiddleware:
    def test_middleware_is_enabled(self, client, settings):
        settings.IP_RESTRICT = True
        settings.IP_RESTRICT_APPS = ["admin"]
        settings.IP_SAFELIST_XFF_INDEX = -2
        assert client.get(reverse("admin:index")).status_code == 401

    def test_applies_to_specified_apps_only(self, rf, settings):
        """Only apps listed in `settings.IP_WHITELIST_APPS` should be ip restricted"""

        settings.IP_RESTRICT = True
        settings.IP_RESTRICT_APPS = ["admin"]
        settings.IP_SAFELIST_XFF_INDEX = -2

        request = rf.get("/")

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == 200

    def test_not_enabled_ifip_restrict_is_false(self, rf, settings):
        settings.IP_RESTRICT = False
        settings.IP_RESTRICT_APPS = ["admin"]
        settings.IP_SAFELIST_XFF_INDEX = -2

        request = rf.get(reverse("admin:index"), HTTP_X_FORWARDED_FOR="")

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == 200

    @pytest.mark.parametrize(
        "xff_header,expected_status",
        (
            ["1.1.1.1, 2.2.2.2, 3.3.3.3", 200],
            ["1.1.1.1", 401],
            [
                "",
                401,
            ],
        ),
    )
    def test_x_forwarded_header(self, rf, settings, xff_header, expected_status):
        settings.IP_RESTRICT = True
        settings.IP_RESTRICT_APPS = ["admin"]
        settings.ALLOWED_IPS = ["2.2.2.2"]
        settings.IP_SAFELIST_XFF_INDEX = -2

        request = rf.get(reverse("admin:index"), HTTP_X_FORWARDED_FOR=xff_header)

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == expected_status

    @pytest.mark.parametrize(
        "allowed_ips,expected_status", ([["2.2.2.2"], 200], [["1.1.1.1"], 401])
    )
    def test_ips(self, rf, settings, allowed_ips, expected_status):
        settings.IP_RESTRICT = True
        settings.IP_RESTRICT_APPS = ["admin"]
        settings.ALLOWED_IPS = allowed_ips
        settings.IP_SAFELIST_XFF_INDEX = -2

        request = rf.get(reverse("admin:index"), HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2, 3.3.3.3")

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == expected_status

        settings.ALLOWED_IPS = ["3.3.3.3"]

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == 401

    @pytest.mark.parametrize(
        "allowed_ips,expected_status", ([["2.2.2.2"], 200], [["1.1.1.1"], 401])
    )
    def test_ip_restricted_path(self, rf, settings, allowed_ips, expected_status):
        settings.IP_RESTRICT = True
        settings.IP_RESTRICT_PATH_NAMES = ["main:show-bookings"]
        settings.ALLOWED_IPS = allowed_ips
        settings.IP_SAFELIST_XFF_INDEX = -2

        request = rf.get(
            reverse("main:show-bookings"), HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2, 3.3.3.3"
        )

        assert IpRestrictionMiddleware(dummy_view)(request).status_code == expected_status
