from custom_usermodel.backends import CustomAuthbrokerBackend
from custom_usermodel.models import User


def test_no_match(transactional_db):
    user1 = User.objects.create(email="hello1@world.com", contact_email="blaa1@world.com")

    user2 = CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "jane.doe-df798b95@id.trade.gov.uk",
            "email": "jane.doe@digital.trade.gov.uk",
            "contact_email": "",
            "first_name": "Jane",
            "last_name": "Doe",
        }
    )

    assert user1 != user2

    assert user2.username == "jane.doe-df798b95@id.trade.gov.uk"
    assert user2.email == "jane.doe@digital.trade.gov.uk"
    assert user2.contact_email == ""
    assert user2.first_name == "Jane"
    assert user2.last_name == "Doe"


def test_match_email(transactional_db):
    user1 = User.objects.create(
        email="jane.doe@digital.trade.gov.uk", contact_email="blaa1@world.com"
    )

    user2 = CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "jane.doe-df798b95@id.trade.gov.uk",
            "email": "jane.doe@digital.trade.gov.uk",
            "contact_email": "",
            "first_name": "Jane",
            "last_name": "Doe",
        }
    )

    assert user1 == user2

    assert user2.username == "jane.doe-df798b95@id.trade.gov.uk"
    assert user2.email == "jane.doe@digital.trade.gov.uk"
    assert user2.contact_email == ""
    assert user2.first_name == "Jane"
    assert user2.last_name == "Doe"


def test_match_username(transactional_db):
    user1 = User.objects.create(
        username="jane.doe-df798b95@id.trade.gov.uk",
        email="jane.smith@digital.trade.gov.uk",
        contact_email="blaa1@world.com",
    )

    user2 = CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "jane.doe-df798b95@id.trade.gov.uk",
            "email": "jane.doe@digital.trade.gov.uk",
            "contact_email": "jane.doe@somewhere.com",
            "first_name": "Jane",
            "last_name": "Doe",
        }
    )

    assert user1 == user2

    assert user2.username == "jane.doe-df798b95@id.trade.gov.uk"
    assert user2.email == "jane.doe@digital.trade.gov.uk"
    assert user2.contact_email == "jane.doe@somewhere.com"
    assert user2.first_name == "Jane"
    assert user2.last_name == "Doe"


def test_match_contact_email(transactional_db):
    user1 = User.objects.create(
        email="blaa@blaa.com", contact_email="jane.doe@digital.trade.gov.uk"
    )

    user2 = CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "jane.doe-df798b95@id.trade.gov.uk",
            "email": "jane.doe@digital.gsi.trade.gov.uk",
            "contact_email": "jane.doe@digital.trade.gov.uk",
            "first_name": "Jane",
            "last_name": "Doe",
        }
    )

    assert user1 == user2

    assert user2.username == "jane.doe-df798b95@id.trade.gov.uk"
    assert user2.email == "jane.doe@digital.gsi.trade.gov.uk"
    assert user2.contact_email == "jane.doe@digital.trade.gov.uk"
    assert user2.first_name == "Jane"
    assert user2.last_name == "Doe"
