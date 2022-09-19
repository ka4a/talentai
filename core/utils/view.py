from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from core.utils.file import get_filename_from_path
from core.utils.image import OpenRequestImageError, upload_image_and_fit_to_jpg


def create_file_download_response(field_file):
    logo_file = getattr(field_file, 'file', None)

    if not logo_file:
        return Response({'detail': _('File not found.')}, 404)

    response = HttpResponse(logo_file, content_type='application/force-download')
    response['Content-Disposition'] = 'inline; filename="{}"'.format(
        get_filename_from_path(logo_file.name)
    )
    return response


def upload_photo_view(request, instance):
    request_image = request.data.get('file')

    try:
        instance.photo = upload_image_and_fit_to_jpg(request_image, 128, 128)
    except OpenRequestImageError as error:
        return Response({'detail': error.message}, status=HTTP_400_BAD_REQUEST)

    instance.save()

    return Response({'detail': _('Saved.')})
