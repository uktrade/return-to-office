from django.contrib.auth import get_user_model

from authbroker_client.backends import AuthbrokerBackend

User = get_user_model()


class CustomAuthbrokerBackend(AuthbrokerBackend):
    @staticmethod
    def get_or_create_user(profile):
        user, created = User.objects.get_or_create(
            **{User.USERNAME_FIELD: profile['user_id']},
            defaults={
                'first_name': profile['first_name'],
                'last_name': profile['last_name']
            })
        if created:
            user.set_unusable_password()
            user.save()
        return user

