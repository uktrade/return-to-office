from django.urls import path

from . import views, views_pra

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("privacy-policy", views.show_privacy_policy, name="show-privacy-policy"),
    path("my-bookings", views.show_bookings, name="show-bookings"),
    path("booking/create-who-for", views.create_booking_who_for, name="booking-create-who-for"),
    path("booking/create-initial", views.create_booking_initial, name="booking-create-initial"),
    path(
        "booking/create-business-unit",
        views.create_booking_business_unit,
        name="booking-create-business-unit",
    ),
    path("booking/create-finalize", views.create_booking_finalize, name="booking-create-finalize"),
    path("booking/<int:pk>/cancel", views.cancel_booking, name="booking-cancel"),
    path(
        "activity-stream/bookings", views.activity_stream_bookings, name="activity-stream-bookings"
    ),
    # PRA views
    path("pra/<int:pk>/view", views_pra.pra_view, name="pra-view"),
    path(
        "pra/<int:pk>/staff-member-approve",
        views_pra.pra_staff_member_approve,
        name="pra-staff-member-approve",
    ),
    path(
        "pra/<int:pk>/staff-member-do-not-approve",
        views_pra.pra_staff_member_do_not_approve,
        name="pra-staff-member-do-not-approve",
    ),
    path(
        "pra/<int:pk>/scs-approve",
        views_pra.pra_scs_approve,
        name="pra-scs-approve",
    ),
    path(
        "pra/<int:pk>/scs-do-not-approve",
        views_pra.pra_scs_do_not_approve,
        name="pra-scs-do-not-approve",
    ),
    path("pra/create-initial", views_pra.create_pra_initial, name="pra-create-initial"),
    path(
        "pra/create-business-unit",
        views_pra.create_pra_business_unit,
        name="pra-create-business-unit",
    ),
    path("pra/create-reason", views_pra.create_pra_reason, name="pra-create-reason"),
    path(
        "pra/create-risk-category",
        views_pra.create_pra_risk_category,
        name="pra-create-risk-category",
    ),
    path(
        "pra/create-prefer-not-to-say",
        views_pra.create_pra_prefer_not_to_say,
        name="pra-create-prefer-not-to-say",
    ),
    path("pra/create-mitigation", views_pra.create_pra_mitigation, name="pra-create-mitigation"),
    path(
        "pra/create-mitigation-approve",
        views_pra.create_pra_mitigation_approve,
        name="pra-create-mitigation-approve",
    ),
    path(
        "pra/create-mitigation-do-not-approve",
        views_pra.create_pra_mitigation_do_not_approve,
        name="pra-create-mitigation-do-not-approve",
    ),
    path("pra/submitted", views_pra.pra_show_thanks, name="pra-show-thanks"),
    # TODO: this can be deleted after migration of data from legacy form has been done
    path("pra/migrate", views_pra.pra_migrate, name="pra-migrate"),
    path("pra/fix", views_pra.pra_fix, name="pra-fix"),
]
