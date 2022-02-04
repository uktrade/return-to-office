from main.models import Booking, DitGroup


def test_booking_on_behalf_of_yourself():
    b = Booking()
    assert b.get_on_behalf_of() == "Yourself"


def test_booking_on_behalf_of_dit_email():
    b = Booking(on_behalf_of_dit_email="jane@example.com")
    assert b.get_on_behalf_of() == "jane@example.com"


def test_booking_on_behalf_of_name():
    b = Booking(on_behalf_of_name="Jane Doe")
    assert b.get_on_behalf_of() == "Jane Doe"


def test_booking_on_behalf_of_name_and_dit_email():
    b = Booking(on_behalf_of_name="Jane Doe", on_behalf_of_dit_email="jane@example.com")
    assert b.get_on_behalf_of() == "Jane Doe (jane@example.com)"


def test_dit_group_business_units_empty():
    dg = DitGroup(business_units="")

    assert dg.get_business_units() == ["Unknown"]


def test_dit_group_business_units_empty_lines():
    dg = DitGroup(business_units="   \n   ")

    assert dg.get_business_units() == ["Unknown"]


def test_dit_group_business_units_none():
    dg = DitGroup(business_units=None)

    assert dg.get_business_units() == ["Unknown"]


def test_dit_group_business_units_not_empty():
    dg = DitGroup(business_units="  one  \n\n two\nthree  \nfour  ")

    assert dg.get_business_units() == ["one", "two", "three", "four"]
