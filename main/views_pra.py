import csv
import datetime
import io

from operator import attrgetter

from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django import forms

from notifications_python_client.notifications import NotificationsAPIClient

from custom_usermodel.models import User

from .forms_pra import (
    PRAFormInitial,
    PRAFormRiskCategory,
    PRAFormMitigation,
    PRAFormMitigationApprove,
    PRAFormMitigationDoNotApprove,
    PRAFormReason,
    PRAFormBusinessUnit,
    PRAFormMigrate,
)

from .models import PRA, DitGroup


# TODO: this can be deleted after migration of data from legacy form has been done
class LegacyPRA:
    RC_MAPPING = {
        "High risk (clinically extremely vulnerable) due to existing health conditions": PRA.RC_HIGH_RISK,
        "Lives with someone at high risk (clinically extremely vulnerable) due to existing health conditions": PRA.RC_LIVES_WITH_HIGH_RISK,
        "Lives with someone at moderate risk (clinically vulnerable)": PRA.RC_LIVES_WITH_MODERATE_RISK,
        "Moderate risk (clinically vulnerable)": PRA.RC_MODERATE_RISK,
        "Falls into one of the categories where evidence suggests that risk may be elevated": PRA.RC_ELEVATED_RISK,
        "Does not fall into any of the above categories ": PRA.RC_NO_CATEGORY,
        "The staff member would prefer not to say": PRA.RC_PREFER_NOT_TO_SAY,
    }

    MO_MAPPING = {
        "I approve - mitigation measures required": PRA.MO_APPROVE_MITIGATION_REQUIRED,
        "N/A - High Risk": PRA.MO_APPROVE_MITIGATION_REQUIRED,
        "I approve  - no mitigation measures required": PRA.MO_APPROVE_NO_MITIGATION,
        "N/A - No Risk Identified": PRA.MO_APPROVE_NO_MITIGATION,
        "I do not approve - mitigation measures explored but considered insufficient ": PRA.MO_DO_NOT_APPROVE,
    }

    # cache for creating new users. key = email, value = User object
    user_cache = {}

    def __init__(self, row_nr, row):
        self.row_nr = row_nr
        self.staff_member_email = row["Staff Member Email Address"].replace(" ", "")
        self.staff_member_name = row["Staff Member Name"]
        self.line_manager_email = row["Line Manager Email Address"].replace(" ", "")
        self.scs_email = row["SCS Email Address"].replace(" ", "")
        self.status = row["Status"]
        self.risk_category = row["Risk Catagory"]
        self.authorized_reason = row["Authorised Reason"]
        self.created = datetime.datetime.strptime(row["Created"], "%d/%m/%Y %H:%M")
        self.mitigation_measures = row["Mitigation Measures Recommended/Considered"]
        self.manager_rec = row["Manager's Recommendation"]

        # str describing action taken/not-taken
        self.desc = ""

        # whether to migrate this record
        self.do_migrate = False

        if self.status in [
            "Approved - Added to Access List",
            "SCS Approve",
            "Pending Staff Member",
            "Pending SCS",
            "Staff Approve",
        ]:
            self.do_migrate = True

        elif self.status in [
            "Tech Fail",
            "Closed - High Risk",
            "Closed - Pending Further Submission",
            "Staff and SCS EMail Match",
            "Closed - LM did not approve",
            "Deleted Record Placeholder",
            "Closed - Refused to take part",
        ]:
            self.desc = "Status in 'do-not-migrate' list"
        else:
            self.desc = f"Unknown status '{self.status}'"

        if self.do_migrate:
            try:
                validate_email(self.staff_member_email)
                validate_email(self.line_manager_email)
                validate_email(self.scs_email)
            except ValidationError:
                self.do_migrate = False
                self.desc = "Invalid staff/line-manager/SCS email address"

        if self.do_migrate:
            # only do these for migrating rows, there's too much crap in the
            # data in the non-migrated rows, it falls over horribly
            self.risk_category = self.RC_MAPPING[self.risk_category]
            self.mitigation_outcome = self.MO_MAPPING[self.manager_rec]

        if self.do_migrate and (self.mitigation_outcome == PRA.MO_DO_NOT_APPROVE):
            self.do_migrate = False
            self.desc = "Manager did not approve"

        if self.do_migrate:
            self.staff_member = User.get_by_email(self.staff_member_email)

            if self.staff_member and self.staff_member.pra_forms.exists():
                self.do_migrate = False
                self.desc = "PRA already exists in the new system"

    def __str__(self):
        return f"LegacyPRA(staff_member_email={self.staff_member_email}, row_nr={self.row_nr})"

    def __repr__(self):
        return str(self)

    def get_or_create_user(self, email):
        user = self.user_cache.get(email)

        if user:
            return user

        user = User.get_by_email(email)

        if user:
            self.user_cache[email] = user
            return user

        user = User.objects.create(email=email)
        user.set_unusable_password()

        self.user_cache[email] = user

        return user

    @classmethod
    def clear_cached_users(cls):
        cls.user_cache.clear()

    @classmethod
    def save_cached_users(cls):
        for user in cls.user_cache.values():
            user.save()

    def prepare_migrate(self):
        assert self.do_migrate

        if not self.staff_member:
            self.staff_member = self.get_or_create_user(self.staff_member_email)

        self.line_manager = self.get_or_create_user(self.line_manager_email)
        self.scs = self.get_or_create_user(self.scs_email)

        if self.status in [
            "Pending Staff Member",
        ]:
            approved_staff_member = None
            approved_scs = None
        elif self.status in [
            "Pending SCS",
            "Staff Approve",
        ]:
            approved_staff_member = True
            approved_scs = None
        elif self.status in [
            "Approved - Added to Access List",
            "SCS Approve",
        ]:
            approved_staff_member = True
            approved_scs = True
        else:
            raise Exception(f"Unexpected status {self.status}")

        self.new_pra = PRA(
            staff_member=self.staff_member,
            scs=self.scs,
            line_manager=self.line_manager,
            group="Unknown (migrated)",
            business_unit="Unknown (migrated)",
            authorized_reason=self.authorized_reason,
            risk_category=self.risk_category,
            mitigation_outcome=self.mitigation_outcome,
            mitigation_measures=self.mitigation_measures,
            approved_staff_member=approved_staff_member,
            approved_scs=approved_scs,
            migrated=True,
        )

    def execute_migrate(self, req):
        assert self.do_migrate

        self.new_pra.save()
        nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        link = req.build_absolute_uri(reverse("main:pra-view", kwargs={"pk": self.new_pra.pk}))

        if self.new_pra.approved_staff_member is None:
            nc.send_email_notification(
                email_address=self.new_pra.staff_member.get_contact_email(),
                template_id="7c663f35-276c-4737-91c5-c0f4b02122bb",
                personalisation={
                    "link": link,
                    "line_manager": self.new_pra.line_manager.full_name(),
                },
            )

            return "Emailed staff member for approval"

        elif self.new_pra.approved_scs is None:
            nc.send_email_notification(
                email_address=self.new_pra.scs.get_contact_email(),
                template_id="9bae5273-ff86-43fd-b67b-1abdc0bea513",
                personalisation={
                    "link": link,
                    "staff_member": self.new_pra.staff_member.full_name(),
                    "line_manager": self.new_pra.line_manager.full_name(),
                },
            )

            return "Emailed SCS for approval"

        return "Approved PRA saved"


def create_pra_initial(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormInitial(req.POST)

        if form.is_valid():
            req.session["pra_staff_member_email"] = form.cleaned_data["staff_member_email"]
            req.session["pra_scs_email"] = form.cleaned_data["scs_email"]
            req.session["pra_dit_group"] = int(form.cleaned_data["dit_group"])

            return redirect(reverse("main:pra-create-business-unit"))
    else:
        if not req.GET.get("back", False):
            clear_pra_session_variables(req)
            initial = None
        else:
            initial = {
                "staff_member_email": req.session["pra_staff_member_email"],
                "scs_email": req.session["pra_scs_email"],
                "dit_group": req.session["pra_dit_group"],
            }

        form = PRAFormInitial(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_initial.html", ctx)


def create_pra_business_unit(req):
    ctx = {}

    dit_group = req.session["pra_dit_group"]

    if req.method == "POST":
        form = PRAFormBusinessUnit(dit_group, req.POST)

        if form.is_valid():
            req.session["pra_business_unit"] = form.cleaned_data["business_unit"]

            return redirect(reverse("main:pra-create-reason"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"business_unit": req.session["pra_business_unit"]}

        form = PRAFormBusinessUnit(dit_group, initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_business_unit.html", ctx)


def create_pra_reason(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormReason(req.POST)

        if form.is_valid():
            req.session["pra_authorized_reason"] = form.cleaned_data["authorized_reason"]

            return redirect(reverse("main:pra-create-risk-category"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"authorized_reason": req.session["pra_authorized_reason"]}

        form = PRAFormReason(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_reason.html", ctx)


def create_pra_risk_category(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormRiskCategory(req.POST)

        if form.is_valid():
            rc = form.cleaned_data["risk_category"]
            req.session["pra_risk_category"] = rc

            if rc == PRA.RC_PREFER_NOT_TO_SAY:
                return redirect(reverse("main:pra-create-prefer-not-to-say"))
            elif rc in (
                PRA.RC_LIVES_WITH_MODERATE_RISK,
                PRA.RC_MODERATE_RISK,
                PRA.RC_ELEVATED_RISK,
            ):
                return redirect(reverse("main:pra-create-mitigation"))
            elif rc in (PRA.RC_HIGH_RISK, PRA.RC_LIVES_WITH_HIGH_RISK, PRA.RC_NO_CATEGORY):
                errors_or_redirect = create_pra_submit(req)

                if isinstance(errors_or_redirect, list):
                    for error in errors_or_redirect:
                        form.add_error(None, error)
                else:
                    return redirect(errors_or_redirect)
            else:
                raise Exception(f"Unknown risk category '{rc}'")
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"risk_category": req.session["pra_risk_category"]}

        form = PRAFormRiskCategory(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_risk_category.html", ctx)


def create_pra_prefer_not_to_say(req):
    ctx = {}

    if req.method == "POST":
        form = forms.Form(req.POST)

        if form.is_valid():
            errors_or_redirect = create_pra_submit(req)

            if isinstance(errors_or_redirect, list):
                for error in errors_or_redirect:
                    form.add_error(None, error)
            else:
                return redirect(errors_or_redirect)
    else:
        form = forms.Form()

    ctx["form"] = form

    return render(req, "main/create_pra_prefer_not_to_say.html", ctx)


def create_pra_mitigation(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormMitigation(req.POST)

        if form.is_valid():
            mo = form.cleaned_data["mitigation_outcome"]
            req.session["pra_mitigation_outcome"] = mo

            if mo == PRA.MO_APPROVE_NO_MITIGATION:
                errors_or_redirect = create_pra_submit(req)

                if isinstance(errors_or_redirect, list):
                    for error in errors_or_redirect:
                        form.add_error(None, error)
                else:
                    return redirect(errors_or_redirect)
            elif mo == PRA.MO_APPROVE_MITIGATION_REQUIRED:
                return redirect(reverse("main:pra-create-mitigation-approve"))
            elif mo == PRA.MO_DO_NOT_APPROVE:
                return redirect(reverse("main:pra-create-mitigation-do-not-approve"))
            else:
                raise Exception(f"Unknown mitigation outcome '{mo}'")
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"mitigation_outcome": req.session["pra_mitigation_outcome"]}

        form = PRAFormMitigation(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_mitigation.html", ctx)


def create_pra_mitigation_approve(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormMitigationApprove(req.POST)

        if form.is_valid():
            req.session["pra_mitigation_measures"] = form.cleaned_data["mitigation_measures"]

            errors_or_redirect = create_pra_submit(req)

            if isinstance(errors_or_redirect, list):
                for error in errors_or_redirect:
                    form.add_error(None, error)
            else:
                return redirect(errors_or_redirect)
    else:
        form = PRAFormMitigationApprove()

    ctx["form"] = form

    return render(req, "main/create_pra_mitigation_approve.html", ctx)


def create_pra_mitigation_do_not_approve(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormMitigationDoNotApprove(req.POST)

        if form.is_valid():
            req.session["pra_mitigation_measures"] = form.cleaned_data["mitigation_measures"]

            errors_or_redirect = create_pra_submit(req)

            if isinstance(errors_or_redirect, list):
                for error in errors_or_redirect:
                    form.add_error(None, error)
            else:
                return redirect(errors_or_redirect)
    else:
        form = PRAFormMitigationDoNotApprove()

    ctx["form"] = form

    return render(req, "main/create_pra_mitigation_do_not_approve.html", ctx)


def create_pra_submit(req: HttpRequest):
    """ Returns either a list[str] of errors, or a str which is a redirect URL."""

    staff_member_email = req.session["pra_staff_member_email"]
    scs_email = req.session["pra_scs_email"]
    dit_group = get_object_or_404(DitGroup, pk=req.session["pra_dit_group"]).name
    business_unit = req.session["pra_business_unit"]
    authorized_reason = req.session["pra_authorized_reason"]
    risk_category = req.session["pra_risk_category"]
    mitigation_outcome = req.session.get("pra_mitigation_outcome", "")
    mitigation_measures = req.session.get("pra_mitigation_measures", "")

    errors = []

    staff_member = User.get_by_email(staff_member_email)
    scs = User.get_by_email(scs_email)

    if not staff_member:
        errors.append(
            f"Staff member '{staff_member_email}' not found; please make sure they have logged in to the system at least once"
        )

    if not scs:
        errors.append(
            f"SCS '{scs_email}' not found; please make sure they have logged in to the system at least once"
        )

    if errors:
        return errors

    pra = PRA(
        staff_member=staff_member,
        scs=scs,
        line_manager=req.user,
        group=dit_group,
        business_unit=business_unit,
        authorized_reason=authorized_reason,
        risk_category=risk_category,
        mitigation_outcome=mitigation_outcome,
        mitigation_measures=mitigation_measures,
        migrated=False,
    )

    pra.save()
    clear_pra_session_variables(req)

    nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

    if pra.needs_staff_member_approval():
        link = req.build_absolute_uri(reverse("main:pra-view", kwargs={"pk": pra.pk}))

        nc.send_email_notification(
            email_address=staff_member.get_contact_email(),
            template_id="7c663f35-276c-4737-91c5-c0f4b02122bb",
            personalisation={
                "link": link,
                "line_manager": pra.line_manager.full_name(),
            },
        )
    else:
        # PRA rejected immediately, do not even ask staff_member for approval, just notify them
        nc.send_email_notification(
            email_address=staff_member.get_contact_email(),
            template_id="72760c96-cc22-4a55-89c0-b5d9dcd6a8ab",
            personalisation={
                "line_manager": pra.line_manager.full_name(),
            },
        )

    return reverse("main:pra-show-thanks")


def pra_show_thanks(req):
    ctx = {}

    return render(req, "main/pra_show_thanks.html", ctx)


def pra_view(req, pk):
    ctx = {}

    pra = get_object_or_404(PRA, pk=pk)

    if req.user not in (pra.staff_member, pra.line_manager, pra.scs):
        raise PermissionDenied

    ctx["pra"] = pra

    return render(req, "main/pra_view.html", ctx)


@require_POST
def pra_staff_member_approve(req, pk):
    return _mark_pra_staff_member_approval(req, pk, True)


@require_POST
def pra_staff_member_do_not_approve(req, pk):
    return _mark_pra_staff_member_approval(req, pk, False)


def _mark_pra_staff_member_approval(req: HttpRequest, pk: int, approval: bool) -> HttpResponse:
    pra = get_object_or_404(PRA, pk=pk)

    if req.user != pra.staff_member:
        raise PermissionDenied

    if not pra.needs_staff_member_approval():
        raise Exception("PRA does not need staff member approval")

    pra.approved_staff_member = approval
    pra.save()

    link = req.build_absolute_uri(reverse("main:pra-view", kwargs={"pk": pra.pk}))

    nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

    nc.send_email_notification(
        email_address=pra.line_manager.get_contact_email(),
        template_id="3c4dfc7b-d978-4268-9c2e-517a41c24b64",
        personalisation={
            "link": link,
            "role": "A staff member",
            "who": pra.staff_member.full_name(),
            "action": "approved" if approval else "rejected",
        },
    )

    if approval:
        nc.send_email_notification(
            email_address=pra.scs.get_contact_email(),
            template_id="9bae5273-ff86-43fd-b67b-1abdc0bea513",
            personalisation={
                "link": link,
                "staff_member": pra.staff_member.full_name(),
                "line_manager": pra.line_manager.full_name(),
            },
        )

    return redirect(reverse("main:pra-view", kwargs={"pk": pra.pk}))


@require_POST
def pra_scs_approve(req, pk):
    return _mark_pra_scs_approval(req, pk, True)


@require_POST
def pra_scs_do_not_approve(req, pk):
    return _mark_pra_scs_approval(req, pk, False)


def _mark_pra_scs_approval(req: HttpRequest, pk: int, approval: bool) -> HttpResponse:
    pra = get_object_or_404(PRA, pk=pk)

    if req.user != pra.scs:
        raise PermissionDenied

    if not pra.needs_scs_approval():
        raise Exception("PRA does not need SCS approval")

    pra.approved_scs = approval
    pra.save()

    link = req.build_absolute_uri(reverse("main:pra-view", kwargs={"pk": pra.pk}))

    nc = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

    nc.send_email_notification(
        email_address=pra.line_manager.get_contact_email(),
        template_id="3c4dfc7b-d978-4268-9c2e-517a41c24b64",
        personalisation={
            "link": link,
            "role": "SCS",
            "who": pra.scs.full_name(),
            "action": "approved" if approval else "rejected",
        },
    )

    return redirect(reverse("main:pra-view", kwargs={"pk": pra.pk}))


# TODO: this can be deleted after migration of data from legacy form has been done
def pra_migrate(req):
    ctx = {}

    if not req.user.is_staff:
        raise PermissionDenied

    if req.method == "POST":
        form = PRAFormMigrate(req.POST, req.FILES)

        if form.is_valid():
            csv_data = io.StringIO(req.FILES["csv_data"].read().decode("utf-8"))
            action = form.cleaned_data["action"]

            # key = staff_member_email, value = LegacyPRA (newest)
            old_pras = {}

            reader = csv.DictReader(csv_data)

            LegacyPRA.clear_cached_users()

            for i, row in enumerate(reader):
                legacy_pra = LegacyPRA(i, row)
                existing_old_pra = old_pras.get(legacy_pra.staff_member_email)

                if existing_old_pra:
                    if legacy_pra.created > existing_old_pra.created:
                        old_pras[legacy_pra.staff_member_email] = legacy_pra
                else:
                    old_pras[legacy_pra.staff_member_email] = legacy_pra

            old_pras = list(old_pras.values())
            old_pras.sort(key=attrgetter("desc"))

            for old_pra in old_pras:
                if old_pra.do_migrate:
                    old_pra.prepare_migrate()

            if action == "check":
                ctx["old_pras"] = old_pras
            elif action == "import":
                # remove ones we don't need to do anything with
                old_pras = [x for x in old_pras if x.do_migrate]

                def process():
                    yield f"Pre-populating {len(LegacyPRA.user_cache)} users...\n"
                    LegacyPRA.save_cached_users()

                    for i, old_pra in enumerate(old_pras):
                        yield f"Processing {i+1}/{len(old_pras)}: {old_pra.staff_member_name} ({old_pra.staff_member_email})..."

                        actions = old_pra.execute_migrate(req) + "\n"
                        yield actions

                    yield "All done!"

                return StreamingHttpResponse(process(), content_type="text/plain; charset=utf-8")
            else:
                raise Exception(f"Unknown action {action}")

    else:
        form = PRAFormMigrate()

    ctx["form"] = form

    return render(req, "main/pra_migrate.html", ctx)


def clear_pra_session_variables(req):
    """Clear PRA flow related session variables."""

    for key in [
        "pra_staff_member_email",
        "pra_scs_email",
        "pra_dit_group",
        "pra_authorized_reason",
        "pra_business_unit",
        "pra_risk_category",
        "pra_mitigation_outcome",
        "pra_mitigation_measures",
    ]:
        if key in req.session:
            del req.session[key]
