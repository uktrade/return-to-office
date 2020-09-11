from django.contrib.auth import get_user_model

from authbroker_client.backends import AuthbrokerBackend
from authbroker_client.utils import get_client, has_valid_token, get_profile

User = get_user_model()


USER_PROFILE_ID_FIELD = "email"


class CustomAuthbrokerBackend(AuthbrokerBackend):
    def authenticate(self, request, **kwargs):
        client = get_client(request)
        if has_valid_token(client):
            profile = get_profile(client)
            return self.get_or_create_user(profile)
        return None

    @staticmethod
    def get_or_create_user(profile):
        user, created = User.objects.get_or_create(
            **{User.USERNAME_FIELD: profile[USER_PROFILE_ID_FIELD]},
            defaults={"first_name": profile["first_name"], "last_name": profile["last_name"]},
        )
        if created:
            user.set_unusable_password()
            user.save()
        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
