from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import User
from core.serializers import UserResetPasswordSerializer
from core.serializers import UserSetPasswordSerializer
from core.utils import set_drf_sensitive_post_parameters
from core.email import send_reset_password_link


class PasswordResetView(viewsets.ViewSet):
    """Endpoint for sending password reset link.

    Based on django.contrib.auth.views.PasswordResetView
    """

    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='user_reset_password', request_body=UserResetPasswordSerializer,
    )
    def reset_password(self, request, format=None):
        serializer = UserResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        send_reset_password_link(
            request,
            serializer.validated_data['email'],
            self.email_template_name,
            self.subject_template_name,
        )

        return Response({'detail': _('Password reset email sent.')})


class PasswordResetConfirmView(viewsets.ViewSet):
    """Endpoint for changing password via reset link.

    Based on django.contrib.auth.views.PasswordResetConfirmView
    """

    token_generator = default_token_generator

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='user_confirm_password_reset',
        request_body=UserSetPasswordSerializer,
    )
    @method_decorator(never_cache)
    def confirm_password_reset(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = UserSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_user(serializer.validated_data['uidb64'])
        token = serializer.validated_data['token']

        if user is None or not self.token_generator.check_token(user, token):
            return Response(
                {'detail': _('Reset link is not valid.')},
                status=status.HTTP_403_FORBIDDEN,
            )

        form = SetPasswordForm(user=user, data=serializer.validated_data)

        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        form.save()
        return Response({'detail': _('Password reset successfully.')})

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            pass
