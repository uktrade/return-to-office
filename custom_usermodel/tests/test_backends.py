from datetime import datetime, timezone
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


def test_duplicate_user_gets_deleted(transactional_db):
    correct_user = User.objects.create(
        username="pete.samuel-df798b95@id.trade.gov.uk",
        last_login="2021-01-01 00:00:00",
        email="pete.samuel@digital.gsi.trade.gov.uk",
        contact_email="pete.samuel@digital.trade.gov.uk",
        first_name="Pete",
        last_name="Samuel",
    )

    correct_user.refresh_from_db()

    incorrect_user = User.objects.create(
        username="pete.samuel-df798b952@id.trade.gov.uk",
        last_login=None,
        email="pete.samuel2@digital.gsi.trade.gov.uk",
        contact_email="pete.samuel@digital.trade.gov.uk",
        first_name="Pete",
        last_name="Samuel",
    )

    incorrect_user.refresh_from_db()

    CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "pete.samuel-df798b95@id.trade.gov.uk",
            "email": "pete.samuel@digital.gsi.trade.gov.uk",
            "contact_email": "pete.samuel@digital.trade.gov.uk",
        }
    )

    user_model_query = User.objects.filter(contact_email="pete.samuel@digital.trade.gov.uk")

    assert user_model_query.count() == 1
    assert user_model_query.first().last_login == datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc)
