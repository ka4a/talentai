from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator


def send_reset_password_link(
    request, email, email_template, subject_template, email_context=None
):
    """Send reset password link, return errors if something is wrong."""

    if email_context is None:
        email_context = {}

    form = PasswordResetForm(data={'email': email})

    if not form.is_valid():
        raise ValidationError(form.errors)

    form.save(
        use_https=request.is_secure(),
        token_generator=default_token_generator,
        email_template_name=email_template,
        subject_template_name=subject_template,
        extra_email_context=email_context,
        request=request,
    )
