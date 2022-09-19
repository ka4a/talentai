import io
import uuid
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _


class OpenRequestImageError(Exception):
    def __init__(self, message):
        self.message = message


def open_request_image(request_image_file):
    if request_image_file is None:
        raise OpenRequestImageError(_('No file in request data.'))

    try:
        image = Image.open(request_image_file)
        image.filename = request_image_file.name
        return image
    except:
        raise OpenRequestImageError(_('Image file is not valid.'))


def to_uploaded_jpeg_file(image):
    rgb_image = to_rgb(image)

    output = io.BytesIO()
    rgb_image.save(output, format='JPEG', quality=80)
    output.seek(0)

    filename = without_extension(image.filename)

    return InMemoryUploadedFile(
        output,
        'ImageField',
        f'{filename}.jpg',
        'image/jpeg',
        output.getbuffer().nbytes,
        None,
    )


WHITE = (255, 255, 255)


def to_rgb(image):
    if image.mode == 'RGB':
        return image

    rgba_image = image.convert('RGBA')
    background = Image.new('RGBA', rgba_image.size, WHITE)

    rgb_image = Image.alpha_composite(background, rgba_image).convert('RGB')
    rgb_image.filename = image.filename

    return rgb_image


def upload_image_and_fit_to_jpg(request_image, width, height, method=Image.ANTIALIAS):
    image = open_request_image(request_image)
    ImageOps.fit(image, size=(width, height), method=method)
    return to_uploaded_jpeg_file(image)


def without_extension(filename):
    dot_index = filename.rfind('.')
    return filename[0:dot_index]
