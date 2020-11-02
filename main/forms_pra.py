from django import forms

# from django.utils.safestring import mark_safe
from django.core.validators import validate_email

from custom_usermodel.models import User

from .models import PRA, DitGroup

from .widgets import GovUKTextInput, GovUKRadioSelect, GovUKTextArea


class PRAFormInitial(forms.Form):
    staff_member_email = forms.CharField(
        widget=GovUKTextInput(),
        label="Staff member email address",
    )

    scs_email = forms.CharField(
        widget=GovUKTextInput(),
        label="SCS email address",
        help_text="Please enter your own email address if you, the line manager, are an SCS member.",
    )

    dit_group = forms.ChoiceField(label="DIT group", widget=GovUKRadioSelect())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["staff_member_email"].widget.form_instance = self
        self.fields["scs_email"].widget.form_instance = self
        self.fields["dit_group"].widget.form_instance = self

        self.fields["dit_group"].choices = [
            (dg.pk, str(dg)) for dg in DitGroup.objects.all().order_by("name")
        ]

    def clean_staff_member_email(self):
        addr = self.cleaned_data["staff_member_email"]
        self._check_user_exists(addr)

        # TODO: should we check staff member does not already have an existing,
        # active PRA in the DB? waiting for sajid to check this with someone

        return addr

    def clean_scs_email(self):
        addr = self.cleaned_data["scs_email"]
        self._check_user_exists(addr)

        return addr

    def _check_user_exists(self, email):
        validate_email(email)

        if (
            not User.objects.filter(contact_email=email).first()
            and not User.objects.filter(email=email).first()
        ):
            raise forms.ValidationError(
                "User not found; please make sure they have logged in to the system at least once"
            )


class PRAFormReason(forms.Form):
    authorized_reason = forms.ChoiceField(
        widget=GovUKRadioSelect(),
        label="Authorised reason for office attendance",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["authorized_reason"].widget.form_instance = self

        self.fields["authorized_reason"].choices = [
            ("Information access requirements", "Information access requirements"),
            ("Essential corporate enabler support", "Essential corporate enabler support"),
            ("Personal circumstances", "Personal circumstances"),
            ("Support to Ministers or Cabinet Office", "Support to Ministers or Cabinet Office"),
            ("Trade negotiations", "Trade negotiations"),
            ("Visitor", "Visitor"),
            ("Facilities Management", "Facilities Management"),
            ("Collect Personal Items", "Collect Personal Items"),
            ("Other", "Other"),
        ]


class PRAFormBusinessUnit(forms.Form):
    business_unit = forms.ChoiceField(label="Business unit", widget=GovUKRadioSelect())

    def __init__(self, dit_group, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["business_unit"].widget.form_instance = self

        self.fields["business_unit"].choices = [
            (x, x) for x in DitGroup.objects.get(pk=dit_group).get_business_units()
        ]


class PRAFormRiskCategory(forms.Form):
    risk_category = forms.ChoiceField(
        widget=GovUKRadioSelect(),
        label="Risk category",
        help_text="The staff member has indicated that they fall into the following risk category",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["risk_category"].widget.form_instance = self

        self.fields["risk_category"].choices = list(PRA.RC_MAPPING.items())


class PRAFormMitigation(forms.Form):
    mitigation_outcome = forms.ChoiceField(
        widget=GovUKRadioSelect(),
        label="Manager's recommendation",
        help_text="I have discussed possible mitigation with the staff member and make the following recommendation",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mitigation_outcome"].widget.form_instance = self

        self.fields["mitigation_outcome"].choices = list(PRA.MO_MAPPING.items())


class PRAFormMitigationApprove(forms.Form):
    mitigation_measures = forms.CharField(
        widget=GovUKTextArea(),
        label="Mitigation arrangements recommended",
        help_text="""Refer to the personal risk assessment guidance document for
        a list of possible mitigation measures. Please outline any you will use
        or set out proposed alternatives. Please do not include any information
        about the medical condition or risk factors. It is the responsibility of
        you as the line manager to ensure mitigation measures are put in place
        prior to the staff member attending the office.""",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mitigation_measures"].widget.form_instance = self


class PRAFormMitigationDoNotApprove(forms.Form):
    mitigation_measures = forms.CharField(
        widget=GovUKTextArea(),
        label="Mitigation measures considered before decision",
        help_text="""Refer to the personal risk assessment guidance document for
        a list of possible mitigation measures. Please explain below why they
        are considered insufficient to enable the person to return to the
        office. Please do not include any information about the medical
        condition or risk factors.""",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mitigation_measures"].widget.form_instance = self