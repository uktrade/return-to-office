from django.contrib.auth import get_user_model


def create_test_user():
    test_user_email = "test@example.com"
    test_password = "test_password"

    test_user, _ = get_user_model().objects.get_or_create(
        username="test_user",
        email=test_user_email,
        last_login="2021-01-01 00:00:00",
        contact_email="john.smith@digital.trade.gov.uk",
        first_name="John",
        last_name="Smith",
        date_joined="2021-01-01 00:00:00",
    )
    test_user.set_password(test_password)
    test_user.save()

    return test_user
