from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_business_units(value):
    business_units = [x.strip() for x in value.strip().split("\n") if x.strip()] if value else []

    if not business_units:
        raise ValidationError("At least one business unit must be defined")


class DitGroup(models.Model):
    class Meta:
        verbose_name = "DIT Group"
        verbose_name_plural = "DIT Groups"

    name = models.CharField(max_length=80, unique=True)

    business_units = models.TextField(
        help_text="One business unit per line", validators=[validate_business_units]
    )

    def __str__(self):
        return self.name

    def get_business_units(self):
        """Get a list of business units for this group."""

        business_units = (
            [x.strip() for x in self.business_units.strip().split("\n") if x.strip()]
            if self.business_units
            else []
        )

        if not business_units:
            # should not happen, but let's not fall over if it does
            business_units.append("Unknown")

        return business_units


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

    # old bookings
    directorate = models.CharField(max_length=80, blank=True, null=True)

    # new bookings
    group = models.CharField(max_length=80, blank=True, null=True)
    business_unit = models.CharField(max_length=80, blank=True, null=True)

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


class PRA(models.Model):
    """Personal risk assessment form."""

    # risk category values
    RC_HIGH_RISK = "high_risk"
    RC_LIVES_WITH_HIGH_RISK = "lives_with_high_risk"
    RC_MODERATE_RISK = "moderate_risk"
    RC_ELEVATED_RISK = "elevated_risk"
    RC_NO_CATEGORY = "no_category"
    RC_PREFER_NOT_TO_SAY = "prefer_not_to_say"

    RC_MAPPING = {
        RC_HIGH_RISK: "High risk (clinically extremely vulnerable) due to existing health conditions",
        RC_LIVES_WITH_HIGH_RISK: "Lives with someone at high risk (clinically extremely vulnerable) due to existing health conditions",
        RC_MODERATE_RISK: "Moderate risk (clinically vulnerable)",
        RC_ELEVATED_RISK: "Falls into one of the categories where evidence suggests that risk may be elevated",
        RC_NO_CATEGORY: "Does not fall into any of the above categories",
        RC_PREFER_NOT_TO_SAY: "The staff member would prefer not to say",
    }

    # mitigation outcome values
    MO_APPROVE_NO_MITIGATION = "approve_no_mitigation"
    MO_APPROVE_MITIGATION_REQUIRED = "approve_mitigation_required"
    MO_DO_NOT_APPROVE = "do_not_approve"

    MO_MAPPING = {
        MO_APPROVE_NO_MITIGATION: "I approve - no mitigation measures required",
        MO_APPROVE_MITIGATION_REQUIRED: "I approve - mitigation measures required",
        MO_DO_NOT_APPROVE: "I do not approve - mitigation measures explored but considered insufficient",
    }

    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, db_index=True, related_name="pra_forms"
    )

    line_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, db_index=True, related_name="+"
    )

    # HR business process
    hrbp_email = models.CharField(max_length=255)

    # SCS = senior civil service
    scs_email = models.CharField(max_length=255)

    # director general/director
    director = models.CharField(max_length=80)

    authorized_reason = models.CharField(max_length=80)

    business_area = models.CharField(max_length=80)

    risk_category = models.CharField(max_length=80)

    mitigation_outcome = models.CharField(max_length=40, blank=True, default="")

    mitigation_measures = models.TextField(blank=True, default="")

    # FIXME: add date submitted, since these are only valid for 3 months
