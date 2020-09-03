from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
]

# FIXME: views needed

# home page with two links:
#   -my bookings
#   -new booking

# new booking
#   -show list of all my bookings in the future (including today)
#   -simple list for now, in future, maybe can cancel them
#
# new booking
#   -select date and building
#   -select floor (show free desks per floor)
#   -get assigned desk
#   -send email confirmation
