from custom_usermodel.models import User


def test_get_contact_email():
    user = User(email="not-a-contact-email@somewhere.com", contact_email="hello@world.com")

    assert user.get_contact_email() == "hello@world.com"


def test_get_contact_email_falls_back_email():
    user = User(email="hello@world.com")

    assert not user.contact_email

    assert user.get_contact_email() == "hello@world.com"
