from django.shortcuts import render, redirect  # , get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms_pra import (
    PRAFormInitial,
    PRAFormRiskCategory,
    PRAFormMitigation,
    PRAFormMitigationApprove,
    PRAFormMitigationDoNotApprove,
    PRAFormReason,
    PRAFormBusinessArea,
)

from .models import PRA


def create_pra_initial(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormInitial(req.POST)

        if form.is_valid():
            req.session["pra_staff_member_email"] = form.cleaned_data["staff_member_email"]
            req.session["pra_scs_email"] = form.cleaned_data["scs_email"]

            return redirect(reverse("main:pra-create-reason"))
    else:
        if not req.GET.get("back", False):
            clear_pra_session_variables(req)
            initial = None
        else:
            initial = {
                "staff_member_email": req.session["pra_staff_member_email"],
                "scs_email": req.session["pra_scs_email"],
            }

        form = PRAFormInitial(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_initial.html", ctx)


def create_pra_reason(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormReason(req.POST)

        if form.is_valid():
            req.session["pra_authorized_reason"] = form.cleaned_data["authorized_reason"]

            return redirect(reverse("main:pra-create-business-area"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"authorized_reason": req.session["pra_authorized_reason"]}

        form = PRAFormReason(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_reason.html", ctx)


def create_pra_business_area(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormBusinessArea(req.POST)

        if form.is_valid():
            req.session["pra_business_area"] = form.cleaned_data["business_area"]

            return redirect(reverse("main:pra-create-risk-category"))
    else:
        if not req.GET.get("back", False):
            initial = None
        else:
            initial = {"business_area": req.session["pra_business_area"]}

        form = PRAFormBusinessArea(initial=initial)

    ctx["form"] = form

    return render(req, "main/create_pra_business_area.html", ctx)


def create_pra_risk_category(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormRiskCategory(req.POST)

        if form.is_valid():
            rc = form.cleaned_data["risk_category"]
            req.session["pra_risk_category"] = rc

            if rc == PRA.RC_PREFER_NOT_TO_SAY:
                return redirect(reverse("main:pra-create-prefer-not-to-say"))
            elif rc in (PRA.RC_MODERATE_RISK, PRA.RC_ELEVATED_RISK):
                return redirect(reverse("main:pra-create-mitigation"))
            elif rc in (PRA.RC_HIGH_RISK, PRA.RC_LIVES_WITH_HIGH_RISK, PRA.RC_NO_CATEGORY):
                return create_pra_submit(req)
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

    return render(req, "main/create_pra_prefer_not_to_say.html", ctx)


def create_pra_mitigation(req):
    ctx = {}

    if req.method == "POST":
        form = PRAFormMitigation(req.POST)

        if form.is_valid():
            mo = form.cleaned_data["mitigation_outcome"]
            req.session["pra_mitigation_outcome"] = mo

            if mo == PRA.MO_APPROVE_NO_MITIGATION:
                return create_pra_submit(req)
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

            return create_pra_submit(req)
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

            return create_pra_submit(req)
    else:
        form = PRAFormMitigationDoNotApprove()

    ctx["form"] = form

    return render(req, "main/create_pra_mitigation_do_not_approve.html", ctx)


@require_POST
def create_pra_submit(req):
    # FIXME: impl:
    #   -check all data is valid
    #     -parse into model format
    #     -check users exist
    #     -check staff member does not have an active PRA in the DB
    #   -save PRA in db
    #   -send email to staff member with link to approve/disapprove the PRA
    #   -clear session variables (clear_pra_session_variables(req))

    return redirect(reverse("main:pra-show-thanks"))


def pra_show_thanks(req):
    ctx = {}

    return render(req, "main/pra_show_thanks.html", ctx)


def clear_pra_session_variables(req):
    """Clear PRA flow related session variables."""

    # TODO: add missing fields here
    for key in [
        "pra_staff_member_email",
        "pra_scs_email",
        "pra_authorized_reason",
        "pra_business_area",
    ]:
        if key in req.session:
            del req.session[key]
