import io
import os
import tempfile

import cloudconvert
from django.conf import settings
from django.core.files import File


# Common exceptions
class ConverterError(Exception):
    """Base PDFConvert API exception, all specific exceptions inherits from it."""


class InputFileError(ConverterError, FileNotFoundError):
    """Input file hasn't been passed"""


class FileAlreadyHasRequiredFormat(ConverterError):
    """Input file already has required format"""


class ExtensionError(ConverterError, TypeError):
    """Unappropriated extension"""


class PDFConverter(object):

    API = cloudconvert.Api(settings.CLOUDCONVERT_API_KEY)

    SUPPORTED_INPUT_FORMATS = (
        'doc',
        'docx',
        'xls',
        'xlsx',
        'txt',
        'odt',
        'rtf',
        'ppt',
        'pptx',
        'jpeg',
        'jpg',
        'png',
        'gif',
    )
    SUPPORTED_OUTPUT_FORMATS = ('pdf', 'txt')

    @classmethod
    def get_temp_file(cls, process):
        """
        Put the file from temporary directory to default media storage
        :param: process (cloudconvert process obj)
        :return: File instance, filename
        """
        with tempfile.TemporaryDirectory() as temp_dir:

            download = process.download(localfile=temp_dir)
            filename = download.data['output']['filename']

            path = temp_dir + '/' + filename
            content = open(path, 'rb')

            return File(content), filename

    @classmethod
    def convert(cls, input_file, output_format='pdf'):
        """
        :param input_file:
        :param output_format:
        :return: file object, their extension
        """
        if not input_file:
            raise InputFileError("Input file hasn't been passed")

        if output_format not in cls.SUPPORTED_OUTPUT_FORMATS:
            raise ExtensionError(
                "Unsupported output format {0}.\n"
                "Supported formats: {1}".format(
                    output_format, cls.SUPPORTED_OUTPUT_FORMATS
                )
            )

        src_filename, ext = os.path.splitext(input_file.name)

        if ext[1:] == output_format:
            raise FileAlreadyHasRequiredFormat(
                'File already is already has {0} extension'.format(output_format)
            )

        # Return file if it already has .pdf extension or unsupported extension
        if ext[1:] not in cls.SUPPORTED_INPUT_FORMATS:
            raise ExtensionError(
                "Unsupported input file format {0}.\n"
                "Supported formats: {1}".format(ext[1:], cls.SUPPORTED_INPUT_FORMATS)
            )

        process = cls.API.convert(
            {
                "inputformat": ext[1:],
                "outputformat": output_format,
                "input": "upload",
                "file": io.BufferedReader(input_file.file.open()),
            }
        )
        process.wait()

        content, filename = cls.get_temp_file(process)

        return content, filename, output_format

    @classmethod
    def create_thumbnail(cls, input_file):
        if not input_file:
            raise InputFileError("Input file hasn't been passed")

        src_filename, ext = os.path.splitext(input_file.name)

        if ext != '.pdf':
            raise ExtensionError(
                "Unsupported input file format {}.\n"
                "Thumbnail may only be created for PDF files".format(ext)
            )

        process = cls.API.convert(
            {
                "inputformat": "pdf",
                "outputformat": "jpg",
                "input": "upload",
                "file": io.BufferedReader(input_file.file.open()),
                "converteroptions": {
                    "density": 600,
                    "quality": 100,
                    "command": "-thumbnail x370 -background white -alpha remove {INPUTFILE}[0] {OUTPUTFILE}",
                },
            }
        )
        process.wait()

        content, filename = cls.get_temp_file(process)

        return content, filename
