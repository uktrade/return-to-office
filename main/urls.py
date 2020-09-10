from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("my-bookings", views.show_bookings, name="show-bookings"),
    path("booking/create-who-for", views.create_booking_who_for, name="booking-create-who-for"),
    path("booking/create-initial", views.create_booking_initial, name="booking-create-initial"),
    path("booking/create-finalize", views.create_booking_finalize, name="booking-create-finalize"),
]
