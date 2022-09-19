from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core import filters as f, serializers as s, models as m
from core.constants import CREATE_UPDATE_ACTIONS, VALIDATE_ACTIONS
from core.mixins import ValidateModelMixin
from core.permissions import StaffAccessPolicy
from core.utils import fix_for_yasg
from core.utils.view import create_file_download_response, upload_photo_view
from core.views.views import User


class StaffViewSet(
    RetrieveModelMixin,
    mixins.ListModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,
    ValidateModelMixin,
):

    permission_classes = (StaffAccessPolicy,)
    search_fields = ('id', 'first_name', 'last_name', 'email')
    # Needed for swagger
    queryset = User.objects.all()
    filterset_class = f.StaffFilterSet
    ordering_fields_mapping = {'id': ('id',), 'name': ('first_name', 'last_name')}

    def get_serializer_class(self):
        """Return different serializer if the action is update."""
        if self.action in CREATE_UPDATE_ACTIONS + VALIDATE_ACTIONS:
            return s.UpdateStaffSerializer
        elif self.action == 'retrieve':
            return s.RetrieveStaffSerializer
        elif self.action == 'avatar_list':
            return s.StaffWithAvatarSerializer
        elif self.action == 'upload_photo':
            return None
        return s.StaffSerializer

    @action(detail=True)
    def photo(self, *args, **kwargs):
        return create_file_download_response(self.get_object().photo)

    @photo.mapping.delete
    def delete_photo(self, *args, **kwargs):
        user = self.get_object()

        user.photo.delete()
        user.save()

        return Response({'detail': _('Saved.')})

    @action(methods=['post'], detail=True, parser_classes=(MultiPartParser,))
    @swagger_auto_schema(
        responses={200: 'OK'},
        consumes=['multipart/form-data'],
        manual_parameters=[
            Parameter(name='file', in_='formData', required=True, type='file')
        ],
    )
    def upload_photo(self, request, *args, **kwargs):
        return upload_photo_view(request, self.get_object())

    @fix_for_yasg
    def get_queryset(self):
        """Get current user org's staff Users."""
        profile = self.request.user.profile
        return profile.org.members.all()

    @action(detail=False)
    def avatar_list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
