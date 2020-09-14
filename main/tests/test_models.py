from main.models import Booking


def test_booking_on_behalf_of_yourself():
    b = Booking()
    assert b.get_on_behalf_of() == "Yourself"


def test_booking_on_behalf_of_dit_email():
    b = Booking(on_behalf_of_dit_email="jane@blaa.com")
    assert b.get_on_behalf_of() == "jane@blaa.com"


def test_booking_on_behalf_of_name():
    b = Booking(on_behalf_of_name="Jane Doe")
    assert b.get_on_behalf_of() == "Jane Doe"


def test_booking_on_behalf_of_name_and_dit_email():
    b = Booking(on_behalf_of_name="Jane Doe", on_behalf_of_dit_email="jane@blaa.com")
    assert b.get_on_behalf_of() == "Jane Doe (jane@blaa.com)"
