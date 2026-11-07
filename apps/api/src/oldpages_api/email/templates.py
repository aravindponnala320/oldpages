from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


def _base_wrapper(title: str, body_html: str) -> str:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<title>{title}</title></head>"
        '<body style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; '
        'background:#f5f6f8; margin:0; padding:24px; color:#111827;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="max-width:560px; margin:0 auto; background:#ffffff; border-radius:12px; '
        'overflow:hidden; border:1px solid #eef0f3;">'
        '<tr><td style="padding:28px 32px 8px 32px;">'
        '<h1 style="margin:0 0 4px 0; font-size:22px; font-weight:700; color:#111827;">OldPages</h1>'
        '<p style="margin:0; color:#6b7280; font-size:13px;">Buy, sell &amp; exchange books near you</p>'
        "</td></tr>"
        f'<tr><td style="padding:16px 32px 32px 32px;">{body_html}</td></tr>'
        '<tr><td style="padding:16px 32px; background:#f9fafb; color:#9ca3af; '
        'font-size:12px; border-top:1px solid #eef0f3;">'
        "If you did not request this, you can safely ignore this email."
        "</td></tr></table></body></html>"
    )


def render_verify_email(verify_url: str) -> RenderedEmail:
    body_html = (
        '<p style="margin:0 0 16px 0; font-size:16px;">Welcome! Please verify your email address '
        "to activate your OldPages account.</p>"
        '<p style="margin:16px 0;">'
        f'<a href="{verify_url}" '
        'style="display:inline-block; background:#2563eb; color:#ffffff; text-decoration:none; '
        'padding:12px 20px; border-radius:8px; font-weight:600;">Verify email</a>'
        "</p>"
        '<p style="margin:16px 0 0 0; font-size:13px; color:#6b7280;">'
        f'Or paste this link into your browser:<br><span style="color:#2563eb; word-break:break-all;">{verify_url}</span>'
        "</p>"
        '<p style="margin:16px 0 0 0; font-size:13px; color:#6b7280;">This link expires in 24 hours.</p>'
    )
    text = (
        "Welcome to OldPages!\n\n"
        f"Verify your email: {verify_url}\n\n"
        "This link expires in 24 hours. If you did not create an account, ignore this email."
    )
    return RenderedEmail(
        subject="Verify your OldPages email",
        html=_base_wrapper("Verify your email", body_html),
        text=text,
    )


def render_password_reset(reset_url: str, expires_minutes: int) -> RenderedEmail:
    body_html = (
        '<p style="margin:0 0 16px 0; font-size:16px;">We received a request to reset your OldPages password. '
        "Click below to set a new one.</p>"
        '<p style="margin:16px 0;">'
        f'<a href="{reset_url}" '
        'style="display:inline-block; background:#2563eb; color:#ffffff; text-decoration:none; '
        'padding:12px 20px; border-radius:8px; font-weight:600;">Reset password</a>'
        "</p>"
        '<p style="margin:16px 0 0 0; font-size:13px; color:#6b7280;">'
        f'Or paste this link into your browser:<br><span style="color:#2563eb; word-break:break-all;">{reset_url}</span>'
        "</p>"
        f'<p style="margin:16px 0 0 0; font-size:13px; color:#6b7280;">'
        f"This link expires in {expires_minutes} minutes. If you did not request a reset, ignore this email — "
        "your password has not been changed."
        "</p>"
    )
    text = (
        "Reset your OldPages password.\n\n"
        f"Reset link: {reset_url}\n\n"
        f"This link expires in {expires_minutes} minutes. If you did not request this, ignore the email."
    )
    return RenderedEmail(
        subject="Reset your OldPages password",
        html=_base_wrapper("Reset your password", body_html),
        text=text,
    )
