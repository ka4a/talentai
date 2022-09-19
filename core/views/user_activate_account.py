from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import User
from core.serializers import UserActivationFormSerializer
from core.user_activation import activate_user
from core.utils import set_drf_sensitive_post_parameters

ACTIVATION_LINK_MAX_AGE = timedelta(days=2)
ACTIVATION_TOKEN_SALT = 'talentai-user-activation-token'


def get_activation_token(user):
    return signing.dumps({'user_id': user.id}, salt=ACTIVATION_TOKEN_SALT)


def get_user_from_activation_token(token):
    try:
        data = signing.loads(
            token, salt=ACTIVATION_TOKEN_SALT, max_age=ACTIVATION_LINK_MAX_AGE
        )
    except signing.BadSignature:
        return

    return User.objects.filter(id=data['user_id'], is_activated=False).first()


def send_activation_link(
    request,
    user,
    email_template='account_activation_email/body.txt',
    subject_template=('account_activation_email/subject.txt'),
    email_context=None,
):
    """Send activation link."""

    if email_context is None:
        email_context = {}

    site_name = get_current_site(request).name

    context = {
        'base_url': settings.BASE_URL,
        'site_name': site_name,
        'user': user,
        'token': get_activation_token(user),
        **email_context,
    }

    subject = loader.render_to_string(subject_template, context)
    subject = ''.join(subject.splitlines())

    body = loader.render_to_string(email_template, context)

    email_message = EmailMultiAlternatives(subject, body, to=[user.email])

    email_message.send()


class ActivateAccountView(viewsets.ViewSet):
    """Endpoint for activating account via link."""

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='user_activate', request_body=UserActivationFormSerializer,
    )
    @method_decorator(never_cache)
    def activate_user(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = UserActivationFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_from_activation_token(serializer.validated_data['token'])

        if user is None:
            return Response(
                {'detail': _('Activation link is not valid.')},
                status=status.HTTP_403_FORBIDDEN,
            )

        activate_user(user)
        return Response({'detail': _('Your account is activated.')})
