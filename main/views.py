from django.shortcuts import render

def index(req):
    # FIXME: implement
    #   -my bookings
    #   -new booking

    ctx = {}
    ctx["name"] = req.user.first_name

    return render(req, "main/index.html", ctx)


def show_bookings(req):
    # FIXME: implement
    #   -show list of all my bookings in the future (including today)
    #   -simple list for now, in future, maybe can cancel them

    ctx = {}
    ctx["name"] = req.user.first_name

    return render(req, "main/show_bookings.html", ctx)

def create_booking(req):
    # FIXME: implement
    #   -select date and building
    #   -select floor (show free desks per floor) (new view)
    #   -submit:
    #     -create booking, show assigned desk (get-after-post, new view)
    #     -send email confirmation

    ctx = {}
    ctx["name"] = req.user.first_name

    return render(req, "main/create_booking.html", ctx)
