from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("my-bookings", views.show_bookings, name="show-bookings"),
    path("booking/create-1", views.create_booking_1, name="booking-create-1"),
    path("booking/create-2", views.create_booking_2, name="booking-create-2"),
]
