from django.utils.translation import gettext_lazy as _
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema

from core.serializers import ClientSettingsSerializer
from core.models import Client
from core.permissions import IsClientAdministrator
from core.mixins import ValidateModelMixin
from core.utils.image import upload_image_and_fit_to_jpg, OpenRequestImageError
from core.utils.view import create_file_download_response


class ClientSettingsViewSet(
    GenericViewSet, ValidateModelMixin, RetrieveModelMixin, UpdateModelMixin
):
    model = Client
    serializer_class = ClientSettingsSerializer
    permission_classes = [IsAuthenticated, IsClientAdministrator]

    def get_object(self):
        return self.request.user.profile.client

    def get_parsers(self):
        if getattr(self, 'action', None) == 'upload_logo':
            return [MultiPartParser()]
        return super().get_parsers()


class ClientSettingsLogoView(APIView):

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, IsClientAdministrator]

    def get_object(self):
        return self.request.user.profile.client

    @swagger_auto_schema(
        operation_id='client_settings_upload_logo',
        consumes=['multipart/form-data'],
        responses={200: 'OK'},
        manual_parameters=[
            Parameter(name='file', in_='formData', required=True, type='file')
        ],
    )
    def post(self, request, *args, **kwargs):

        client = self.get_object()
        request_image = request.data.get('file')

        try:
            client.logo = upload_image_and_fit_to_jpg(request_image, 128, 128)
        except OpenRequestImageError as error:
            return Response({'detail': error.message}, 400)

        client.save()
        return Response({'detail': _('Saved.')})

    @swagger_auto_schema(
        operation_id='client_settings_delete_logo', responses={200: 'OK'},
    )
    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        client.logo.delete()

        return Response({'detail': _('Saved.')})

    @swagger_auto_schema(
        operation_id='client_settings_download_logo', responses={200: 'OK'},
    )
    def get(self, request, *args, **kwargs):
        client = self.get_object()

        return create_file_download_response(client.logo)
