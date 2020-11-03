from custom_usermodel.models import User


def test_get_contact_email():
    user = User(email="not-a-contact-email@somewhere.com", contact_email="hello@world.com")

    assert user.get_contact_email() == "hello@world.com"


def test_get_contact_email_falls_back_email():
    user = User(email="hello@world.com")

    assert not user.contact_email

    assert user.get_contact_email() == "hello@world.com"


def test_get_by_email_contact(db):
    user1 = User.objects.create(email="hello1@world.com", contact_email="blaa1@world.com")
    User.objects.create(email="hello2@world.com", contact_email="blaa2@world.com")

    assert User.get_by_email("hello1@world.com") == user1


def test_get_by_email_non_contact(db):
    user1 = User.objects.create(email="hello1@world.com", contact_email="blaa1@world.com")
    User.objects.create(email="hello2@world.com", contact_email="blaa2@world.com")

    assert User.get_by_email("blaa1@world.com") == user1


def test_get_by_email_none(db):
    User.objects.create(email="hello1@world.com", contact_email="blaa1@world.com")
    User.objects.create(email="hello2@world.com", contact_email="blaa2@world.com")

    assert User.get_by_email("blaa3@world.com") is None
