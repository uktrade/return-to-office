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
    path("pra/create-initial", views_pra.create_pra_initial, name="pra-create-initial"),
    path("pra/create-reason", views_pra.create_pra_reason, name="pra-create-reason"),
    path(
        "pra/create-business-area",
        views_pra.create_pra_business_area,
        name="pra-create-business-area",
    ),
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
    path("pra/create-submit", views_pra.create_pra_submit, name="pra-create-submit"),
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
]
