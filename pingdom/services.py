from django.db import DatabaseError


class CheckDatabase:
    name = "database"

    def check(self):
        # TODO: implement pingdom checks
        return True, ""

        # try:
        #     FinancialYear.objects.all().exists()
        #     return True, ""
        # except DatabaseError as e:
        #     return False, e


services_to_check = (CheckDatabase,)
