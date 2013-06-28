from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings
from django.template.loader import get_template_from_string, Context
from django.contrib.staticfiles.finders import (get_finders,
        AppDirectoriesFinder, FileSystemFinder)

from . import BaseProcessor
from ..lib.directive_processor import DirectiveProcessor


class DjangoDirectiveProcessor(DirectiveProcessor):
    """
    Extends the Sprockets-like DirectiveProcessor to add a couple of
    Django-specific features:
    1. The `load_paths` are automatically configured based on the
       configured staticfiles directory
    2. Any files which end `.djtmpl.js` are first processed with the
       template renderer
    """

    DJANGO_TEMPLATE_SUFFIX = '.djtmpl.js'

    def __init__(self):
        load_paths = []
        for finder in get_finders():
            if isinstance(finder, (AppDirectoriesFinder, FileSystemFinder)):
                for storage in finder.storages.values():
                    load_paths.append(storage.location)
        super(DjangoDirectiveProcessor, self).__init__(load_paths=load_paths)

    def get_file_contents(self, path):
        contents = super(DjangoDirectiveProcessor, self).get_file_contents(path)
        if path.endswith(self.DJANGO_TEMPLATE_SUFFIX):
            template = get_template_from_string(contents)
            context = getattr(settings, 'STATICFILESPLUS_JS_CONTEXT', {})
            context.setdefault('settings', settings)
            contents = template.render(Context(context))
        return contents


class JavaScriptProcessor(BaseProcessor):
    original_suffix = '.js'
    processed_suffix = '.js'

    directive_processor = None

    def is_ignored_file(self, path):
        return any(part.startswith('_') for part in path.split(os.sep))

    def process_file(self, input_path, output_path):
        if not self.directive_processor:
            self.directive_processor = DjangoDirectiveProcessor()
        with open(output_path, 'wb') as f:
            contents = self.directive_processor.load(input_path)
            f.write(contents.encode('utf-8'))

