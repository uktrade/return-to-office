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
    name = models.CharField(max_length=60)
    nr_of_desks = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_index=True, related_name="+")

    # if either is non-null, means user booked on behalf of someone else. both
    # can be filled. latter one is not filled for non-dit visitors.
    on_behalf_of_name = models.CharField(max_length=80, blank=True, null=True)
    on_behalf_of_dit_email = models.CharField(max_length=80, blank=True, null=True)

    booking_date = models.DateField(db_index=True)

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="+")

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="+")

    directorate = models.CharField(max_length=80)

    booked_timestamp = models.DateTimeField(auto_now_add=True)
