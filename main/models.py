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
    # becomes False if booking is canceled
    is_active = models.BooleanField(default=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, db_index=True, related_name="+"
    )

    # if either is non-null, means user booked on behalf of someone else. both
    # can be filled. latter one is not filled for non-dit visitors.
    on_behalf_of_name = models.CharField(max_length=80, blank=True, null=True)
    on_behalf_of_dit_email = models.CharField(max_length=80, blank=True, null=True)

    booking_date = models.DateField(db_index=True)

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="+")

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="+")

    directorate = models.CharField(max_length=80)

    booked_timestamp = models.DateTimeField(auto_now_add=True)
    canceled_timestamp = models.DateTimeField(null=True)

    def get_on_behalf_of(self):
        """Return a string describing who the booking is on behalf of. It will be one of:

        "Yourself"
        "Donald Duck"
        "donald.duck@digital.trade.gov.uk"
        "Donald Duck (donald.duck@digital.trade.gov.uk)"
        """

        if self.on_behalf_of_name or self.on_behalf_of_dit_email:
            if self.on_behalf_of_name:
                if self.on_behalf_of_dit_email:
                    return "%s (%s)" % (self.on_behalf_of_name, self.on_behalf_of_dit_email)
                else:
                    return self.on_behalf_of_name
            else:
                return self.on_behalf_of_dit_email
        else:
            return "Yourself"
