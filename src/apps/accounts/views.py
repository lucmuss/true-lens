from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.security.forms import CaptchaInlineForm
from apps.security.services import create_captcha_inline, verify_captcha_inline

from .models import RecruiterSecurityVerification


def security_verify(request: HttpRequest, token: str) -> HttpResponse:
    verification = get_object_or_404(RecruiterSecurityVerification, token=token)
    if verification.is_completed:
        messages.success(request, "Sicherheitsverifikation bereits abgeschlossen.")
        return redirect("account_login")

    captcha_data = create_captcha_inline(request)
    form = CaptchaInlineForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        captcha_ok = verify_captcha_inline(
            request,
            form.cleaned_data["captcha_id"],
            form.cleaned_data["captcha_answer"],
        )
        if not captcha_ok:
            messages.error(request, "Captcha ungueltig.")
        elif verification.is_expired():
            messages.error(request, "Der Sicherheitscode ist abgelaufen.")
        elif form.cleaned_data["code"] != verification.code:
            messages.error(request, "Der Sicherheitscode ist ungueltig.")
        else:
            verification.mark_completed()
            verification.recruiter.is_verified_recruiter = True
            verification.recruiter.save(update_fields=["is_verified_recruiter"])
            messages.success(request, "Verifikation erfolgreich. Du kannst jetzt abstimmen.")
            return redirect("account_login")

    return render(
        request,
        "accounts/security_verify.html",
        {
            "verification": verification,
            "captcha_data": captcha_data,
            "form": form,
        },
    )


@login_required
def recruiter_settings(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        request.user.notify_on_vote_overlap = bool(request.POST.get("notify_on_vote_overlap"))
        request.user.notify_on_contact_requests = bool(request.POST.get("notify_on_contact_requests"))
        request.user.notify_on_security = bool(request.POST.get("notify_on_security"))
        request.user.save(update_fields=["notify_on_vote_overlap", "notify_on_contact_requests", "notify_on_security"])
        messages.success(request, "Einstellungen gespeichert.")
        return redirect("recruiter_settings")
    return render(request, "accounts/settings.html")


@login_required
def delete_recruiter_profile(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        request.user.email = f"deleted-{request.user.pk}@invalid.local"
        request.user.display_name = "deleted"
        request.user.deleted_at = timezone.now()
        request.user.is_active = False
        request.user.save(update_fields=["email", "display_name", "deleted_at", "is_active"])
        messages.success(request, "Profil wurde geloescht. Bestehende Votes bleiben anonym erhalten.")
        return redirect("landing")
    return render(request, "accounts/delete_confirm.html")
