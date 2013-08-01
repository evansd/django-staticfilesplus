from __future__ import absolute_import, unicode_literals

import tempfile
import shutil

import django
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import finders, storage
# In Django 1.4 we can't use the override_settings decorator
# with SimpleTestCase instances so we have to use a
# TransactionTestCase, even though we don't touch the db
if django.VERSION[:2] > (1, 4):
    from django.test import SimpleTestCase
else:
    from django.test import TransactionTestCase as SimpleTestCase


@override_settings(
    STATICFILES_FINDERS=(
        'staticfilesplus.finders.FileSystemFinder',
        'staticfilesplus.finders.AppDirectoriesFinder',
    )
)
class BaseStaticfilesPlusTest(SimpleTestCase):

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
        # Make a temporary directory
        cls.tmp = tempfile.mkdtemp()
        super(BaseStaticfilesPlusTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(BaseStaticfilesPlusTest, cls).tearDownClass()
        # Remove temporary directory
        shutil.rmtree(cls.tmp)
        # Restore monkey-patched values
        if hasattr(cls, '_original_get_finder'):
            finders.get_finder = cls._original_get_finder
            del cls._original_get_finder
        if hasattr(cls, '_original_staticfiles_storage'):
            storage.staticfiles_storage = cls._original_staticfiles_storage
            del cls._original_staticfiles_storage

    def setUp(self):
        settings.STATIC_ROOT = self.tmp_dir()
        settings.STATICFILES_DIRS = (self.tmp_dir(),)
        # Configure a new lazy storage instance so it will pick up our
        # new settings
        storage.staticfiles_storage = storage.ConfiguredStorage()

    def tmp_dir(self):
        return tempfile.mkdtemp(dir=self.tmp)
