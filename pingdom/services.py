from django.db import DatabaseError

from main.models import Building


class CheckDatabase:
    name = "database"

    def check(self):
        try:
            Building.objects.all().exists()
            return True, ""
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase,)
