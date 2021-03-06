from __future__ import absolute_import, unicode_literals

import os
import errno

from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command

from staticfilesplus.processors import BaseProcessor

from .utils import BaseStaticfilesPlusTest


class SimpleTestProcessor(BaseProcessor):

    original_suffix = '.original'
    processed_suffix = '.processed'
    string_to_add = 'processed\n'

    def process_file(self, input_path, output_path):
        with open(output_path, 'wb') as out_file:
            with open(input_path, 'rb') as in_file:
                out_file.write(self.string_to_add.encode('utf8'))
                out_file.write(in_file.read())

    def is_ignored_file(self, path):
        return path.endswith('.ignore' + self.original_suffix)

# We define another processsor with the same output suffix, but a
# a different original suffix as might be the case if you have
# two CSS preprocessors (.less and .scss) both producing .css files
class AnotherTestProcessor(SimpleTestProcessor):

    original_suffix = '.another'
    string_to_add = 'another processor\n'

@override_settings(
    STATICFILESPLUS_PROCESSORS=(
        SimpleTestProcessor,
        AnotherTestProcessor
    )
)
class ProcessorTest(BaseStaticfilesPlusTest):

    def get_file_contents(self, name):
        path = finders.find(name)
        if path is None:
            return None
        with open(path, 'rb') as f:
            return f.read().decode('utf8')

    def write_contents(self, path, contents):
        with open(path, 'wb') as f:
            f.write(contents.encode('utf8'))


    def test_finds_and_processes_file(self):
        contents = 'some text'
        for n, processor in enumerate(settings.STATICFILESPLUS_PROCESSORS):
            name = 'test{}'.format(n)
            original_path = os.path.join(
                    settings.STATICFILES_DIRS[0],
                    name + processor.original_suffix)
            self.write_contents(original_path, contents)
            self.assertEqual(processor.string_to_add + contents,
                             self.get_file_contents(name + processor.processed_suffix))

    def test_finds_already_processesed_file(self):
        contents = 'some processed text'
        name = 'already-processed' + SimpleTestProcessor.processed_suffix
        original_path = os.path.join(settings.STATICFILES_DIRS[0], name)
        self.write_contents(original_path, contents)
        self.assertEqual(contents, self.get_file_contents(name))

    def test_does_not_find_ignored_file(self):
        for n, processor in enumerate(settings.STATICFILESPLUS_PROCESSORS):
            name = 'file{}.ignore'.format(n)
            original_path = os.path.join(settings.STATICFILES_DIRS[0],
                    name + processor.original_suffix)
            self.write_contents(original_path, 'text here')
            self.assertEqual(None, self.get_file_contents(
                name + processor.processed_suffix))


class CollectStaticTest(ProcessorTest):
    """
    Run the same tests as above, but using the collectstatic command
    and inspecting the output in the collected files directory
    """

    def get_file_contents(self, name):
        call_command('collectstatic', interactive=False, verbosity=0)
        path = os.path.join(settings.STATIC_ROOT, name)
        try:
            with open(path, 'rb') as f:
                return f.read().decode('utf8')
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return None
