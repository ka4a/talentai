from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.serializers import UserChangePasswordSerializer
from core.utils import set_drf_sensitive_post_parameters


class PasswordChangeView(viewsets.ViewSet):
    """Endpoint for changing password of logged in user.

    Based on django.contrib.auth.views.PasswordChangeView
    """

    permission_classes = (IsAuthenticated,)

    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        operation_id='user_change_password', request_body=UserChangePasswordSerializer,
    )
    def change_password(self, request, format=None):
        set_drf_sensitive_post_parameters(request)

        serializer = UserChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = PasswordChangeForm(user=request.user, data=serializer.validated_data)

        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        form.save()

        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        return Response({'detail': _('Password changed.')})
