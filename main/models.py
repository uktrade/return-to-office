from django.conf import settings
from django.db import models


class Building(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

class Floor(models.Model):
    class Meta:
        unique_together = [["building", "name"]]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="floors")
    name = models.CharField(max_length=20)

    # for now, a newline-separated list of desk IDs
    desks = models.TextField()

    def __str__(self):
        return self.name

    def nr_of_desks(self):
        """Get number of desks."""

        return len(self.desks.split("\n"))

    def get_free_desk(self, used_desks):
        """Given used_desks (set of used desks), return a random free desk.

        Raises exception if no free desks available."""

        all_desks = set(self.desks.split("\n"))

        free_desks = all_desks - used_desks

        return free_desks.pop()


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_index=True, related_name="+")

    booking_date = models.DateField(db_index=True)

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="+")

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="+")

    desk = models.CharField(max_length=20)

    booked_timestamp = models.DateTimeField(auto_now_add=True)
