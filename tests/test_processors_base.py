from __future__ import absolute_import, unicode_literals

from unittest import TestCase

from staticfilesplus.processors import BaseProcessor


class TestProcessor(BaseProcessor):
    original_suffix = '.orig'
    processed_suffix = '.proc'

processor = TestProcessor()


class BaseProcessorTest(TestCase):

    def test_original_from_processed_name(self):
        self.assertEqual(processor.get_original_name('somefile.proc'),
                         'somefile.orig')

    def test_processed_from_original_name(self):
        self.assertEqual(processor.get_processed_name('otherfile.orig'),
                         'otherfile.proc')

    def test_get_original_ignores_unknown_file(self):
        self.assertEqual(processor.get_original_name('otherfile.foo'),
                         None)

    def test_get_processed_ignores_unknown_file(self):
        self.assertEqual(processor.get_processed_name('otherfile.foo'),
                         None)
