from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
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
)

from .models import PRA, DitGroup


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
