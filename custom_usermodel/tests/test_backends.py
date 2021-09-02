import pytest

from django.test import TestCase
from datetime import datetime, timezone
from custom_usermodel.backends import CustomAuthbrokerBackend
from custom_usermodel.models import User
from main.tests.utils import create_test_user


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


class TestUserRecords(TestCase):
    def setUp(self):
        self.test_user = create_test_user()

    def test_create_new_user_record(self):
        self.client.force_login(self.test_user)
        assert User.objects.all().count() == 1

    def test_user_login_updates_record(self):
        self.client.force_login(self.test_user)
        assert User.objects.first().last_login.date() == datetime.now().date()

    def test_new_user_has_correct_details(self):
        self.client.force_login(self.test_user)
        assert User.objects.first().email == "test@test.com"


def test_duplicate_user_gets_deleted(transactional_db):
    full_details_user = User.objects.create(  # noqa: F841
        username="john.smith-df798b95@id.trade.gov.uk",
        last_login="2021-01-01 00:00:00",
        email="john.smith@digital.gsi.trade.gov.uk",
        contact_email="john.smith@digital.trade.gov.uk",
        first_name="John",
        last_name="Smith",
    )

    partial_details_user = User.objects.create(  # noqa: F841
        username=None,
        last_login=None,
        email="john.smith2@digital.gsi.trade.gov.uk",
        contact_email="john.smith@digital.trade.gov.uk",
        first_name="John",
        last_name="Smith",
    )

    CustomAuthbrokerBackend.get_or_create_user(
        {
            "email_user_id": "john.smith-df798b95@id.trade.gov.uk",
            "email": "john.smith@digital.gsi.trade.gov.uk",
            "contact_email": "john.smith@digital.trade.gov.uk",
            "first_name": "John",
            "last_name": "Smith",
            "username": "john.smith-df798b95@id.trade.gov.uk",
            "last_login": "2021-01-01 00:00:00",
        }
    )

    user_model_query = User.objects.filter(contact_email="john.smith@digital.trade.gov.uk")

    assert user_model_query.count() == 1
    assert user_model_query.first().last_login == datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_assert_raised_by_more_than_one_user(transactional_db):
    with pytest.raises(AssertionError):
        complete_user_record = User.objects.create(  # noqa: F841
            username="john.doe-df798b95@id.trade.gov.uk",
            last_login="2021-01-01 00:00:00",
            email="john.doe@digital.gsi.trade.gov.uk",
            contact_email="john.doe@digital.trade.gov.uk",
            first_name="John",
            last_name="Doe",
        )

        partial_user_record_1 = User.objects.create(  # noqa: F841
            username="john.doe-df798b952@id.trade.gov.uk",
            last_login=None,
            email="john.doe2@digital.gsi.trade.gov.uk",
            contact_email="john.doe@digital.trade.gov.uk",
            first_name="John",
            last_name="Doe",
        )

        partial_user_record_2 = User.objects.create(  # noqa: F841
            username="john.doe-df798b953@id.trade.gov.uk",
            last_login="2021-01-01 00:00:00",
            email="john.doe3@digital.gsi.trade.gov.uk",
            contact_email="john.doe@digital.trade.gov.uk",
            first_name="John",
            last_name="Doe",
        )

        CustomAuthbrokerBackend.get_or_create_user(
            {
                "email_user_id": "john.doe-df798b95@id.trade.gov.uk",
                "email": "john.doe@digital.gsi.trade.gov.uk",
                "contact_email": "john.doe@digital.trade.gov.uk",
            }
        )
