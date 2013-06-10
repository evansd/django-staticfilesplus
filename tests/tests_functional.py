from __future__ import absolute_import, unicode_literals

import os
import errno
import tempfile
import shutil

import django
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.core.management import call_command
# In Django 1.4 we can't use the override_settings decorator
# with SimpleTestCase instances so we have to use a
# TransactionTestCase, even though we don't touch the db
if django.VERSION[:2] > (1, 4):
    from django.test import SimpleTestCase
else:
    from django.test import TransactionTestCase as SimpleTestCase

from staticfilesplus.processors import BaseProcessor


class SimpleTestProcessor(BaseProcessor):

    original_suffix = '.original'
    processed_suffix = '.processed'

    def process_file(self, input_path, output_path):
        with open(output_path, 'wb') as out_file:
            with open(input_path, 'rb') as in_file:
                out_file.write('processed\n'.encode('utf8'))
                out_file.write(in_file.read())

    def is_ignored_file(self, path):
        return path.endswith('.ignore' + self.original_suffix)


@override_settings(
        STATICFILESPLUS_PROCESSORS=(SimpleTestProcessor,),
        STATICFILES_FINDERS=('staticfilesplus.finders.FileSystemFinder',)
)
class ProcessorTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        """
        A necessary evil: monkey-patch various memoized functions to prevent
        test state leaking out. We store the originals and replce them when
        we're done.
        """
        if not hasattr(cls, '_original_get_finder'):
            cls._original_get_finder = finders.get_finder
            # Replace memoized version with the underlying function
            finders.get_finder = finders._get_finder
        if not hasattr(cls, '_original_staticfiles_storage'):
            cls._original_staticfiles_storage = storage.staticfiles_storage
        super(ProcessorTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(ProcessorTest, cls).tearDownClass()
        # Restore monkey-patched values
        if hasattr(cls, '_original_get_finder'):
            finders.get_finder = cls._original_get_finder
            del cls._original_get_finder
        if hasattr(cls, '_original_staticfiles_storage'):
            storage.staticfiles_storage = cls._original_staticfiles_storage
            del cls._original_staticfiles_storage

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        settings.STATIC_ROOT = self.tmp_dir('static_root')
        settings.STATICFILES_DIRS = (self.tmp_dir('static_dir'),)
        # Configure a new lazy storage instance so it will pick up our
        # new settings
        storage.staticfiles_storage = storage.ConfiguredStorage()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def tmp_dir(self, name):
        tmp_dir = os.path.join(self.tmp, name)
        os.mkdir(tmp_dir)
        return tmp_dir

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
        name = 'test1'
        original_path = os.path.join(settings.STATICFILES_DIRS[0], name + '.original')
        self.write_contents(original_path, contents)
        self.assertEqual('processed\n' + contents,
                         self.get_file_contents(name + '.processed'))

    def test_finds_already_processesed_file(self):
        contents = 'some processed text'
        name = 'already-processed.processed'
        original_path = os.path.join(settings.STATICFILES_DIRS[0], name)
        self.write_contents(original_path, contents)
        self.assertEqual(contents, self.get_file_contents(name))

    def test_does_not_find_ignored_file(self):
        name = 'file.ignore'
        original_path = os.path.join(settings.STATICFILES_DIRS[0], name + '.original')
        self.write_contents(original_path, 'text here')
        self.assertEqual(None, self.get_file_contents(name + '.processed'))


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
