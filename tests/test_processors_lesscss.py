from __future__ import absolute_import, unicode_literals

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.test import SimpleTestCase
from django.test.utils import override_settings

from staticfilesplus.processors.lesscss import LessCSSProcessor


@override_settings(STATICFILESPLUS_LESSCSS_COMPRESS=False)
class LessCSSProcessorTest(SimpleTestCase):

    @patch('staticfilesplus.processors.lesscss.subprocess', autospec=True)
    def test_calls_out_to_lessc(self, mock_subprocess):
        LessCSSProcessor().process_file('inpath', 'outpath')
        mock_subprocess.check_call.assert_called_with(
                ['lessc', 'inpath', 'outpath'])

    @patch('staticfilesplus.processors.lesscss.subprocess', autospec=True)
    def test_compress_setting(self, mock_subprocess):
        with override_settings(STATICFILESPLUS_LESSCSS_COMPRESS=True):
            LessCSSProcessor().process_file('inpath', 'outpath')
        mock_subprocess.check_call.assert_called_with(
                ['lessc', '--compress', 'inpath', 'outpath'])

    def test_ignores_paths_with_underscores(self):
        processor = LessCSSProcessor()
        self.assertTrue(processor.is_ignored_file('_dir/path/file'))
        self.assertTrue(processor.is_ignored_file('dir/path/_file'))

    def test_does_not_ignore_paths_without_underscores(self):
        processor = LessCSSProcessor()
        self.assertFalse(processor.is_ignored_file('dir_/path/file'))
        self.assertFalse(processor.is_ignored_file('dir/path_sep/file'))
