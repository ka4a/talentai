import tempfile
from unittest.mock import patch
from os import path

from django.conf import settings
from django.core.files import File
from django.test import TestCase, override_settings

from core.converter import PDFConverter, FileAlreadyHasRequiredFormat
from core.fixtures import create_candidate, create_agency


class PDFConverterTestCase(TestCase):
    def get_file_mock(self, type):
        name = f'{type}file.{type}'
        file_path = path.join(settings.BASE_DIR, f'core/tests/dummies/{name}')

        file = open(f'{file_path}', 'rb')

        return File(file), name

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('core.converter.PDFConverter.API')
    def test_pdf_is_not_converted(self, mock_api):
        """cloudconvert.Api.convert() method shouldn't be called
        if file ext isn't one of (doc, docx, xls, xlsx)
        """
        c = create_candidate(organization=create_agency())
        content, filename = self.get_file_mock('pdf')
        c.resume.save(filename, content)
        with self.assertRaises(FileAlreadyHasRequiredFormat):
            PDFConverter.convert(c.resume)

        mock_api.convert.assert_not_called()

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('core.converter.PDFConverter.get_temp_file')
    @patch('core.converter.PDFConverter.API')
    def test_docx_is_converted(self, mock_api, mock_get_temp_file):
        """cloudconvert.Api.convert() method should be called
        if file ext is one of (doc, docx, xls, xlsx)
        """
        c = create_candidate(organization=create_agency())
        content, filename = self.get_file_mock('docx')
        mock_get_temp_file.return_value = content, filename
        c.resume.save(filename, content)
        PDFConverter.convert(c.resume)

        mock_api.convert.assert_called_once()
