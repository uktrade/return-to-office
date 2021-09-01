from django.contrib.auth import get_user_model
from django.db.models import Q

from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import get_client, has_valid_token, get_profile

User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.get_or_create_user(profile)
        return None

    @staticmethod
    def get_or_create_user(profile):
        # example values:
        #
        # {'email': 'jane.doe@digital.trade.gov.uk',
        #  'user_id': 'df798b95-56cd-4b4a-b549-9e4d98a31ef3',
        #  'email_user_id': 'jane.doe-df798b95@id.trade.gov.uk',

        # these are guaranteed to always be present
        assert profile["email_user_id"]
        assert profile["email"]
        query = (
            Q(username=profile["email_user_id"])
            | Q(email=profile["email"])
            | Q(contact_email=profile["email"])
        )

        # ...whereas this is not
        if profile["contact_email"]:
            query |= Q(contact_email=profile["contact_email"])

        users = User.objects.filter(query)

        # TODO - add comment
        if users.count() > 1:
            for user in users:
                if user.last_login is None:
                    user.delete()

        users.refresh_from_db()

        assert users.count() == 1 or users.count() == 0

        user = users.first()

        if user:
            # this is now the preferred option for the user id
            user.username = profile["email_user_id"]

            # these might change over time, so update them every time
            user.email = profile["email"]
            user.contact_email = profile["contact_email"]
            user.first_name = profile["first_name"]
            user.last_name = profile["last_name"]
        else:
            user = User(
                username=profile["email_user_id"],
                email=profile["email"],
                contact_email=profile["contact_email"],
                first_name=profile["first_name"],
                last_name=profile["last_name"],
            )

            user.set_unusable_password()

        user.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
