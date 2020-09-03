from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("my-bookings", views.show_bookings, name="show-bookings"),
    path("booking/create", views.create_booking, name="booking-create"),
]

# FIXME: views needed


# new booking
#   -show list of all my bookings in the future (including today)
#   -simple list for now, in future, maybe can cancel them
#
# new booking
#   -select date and building
#   -select floor (show free desks per floor)
#   -get assigned desk
#   -send email confirmation
