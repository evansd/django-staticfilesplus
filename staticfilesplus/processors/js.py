from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings
from django.template.loader import get_template_from_string, Context

from . import BaseProcessor
from ..lib.directive_processor import DirectiveProcessor
from ..utils import get_staticfiles_dirs, call_command


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
        staticfiles_dirs = get_staticfiles_dirs()
        super(DjangoDirectiveProcessor, self).__init__(load_paths=staticfiles_dirs)

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
        # Initialise DirectiveProcessor if not already done so
        if not self.directive_processor:
            self.directive_processor = DjangoDirectiveProcessor()
        compress = getattr(settings, 'STATICFILESPLUS_JS_COMPRESS',
                not settings.DEBUG)
        with open(output_path, 'wb') as f:
            contents = self.directive_processor.load(input_path)
            if compress:
                contents = self.compress(contents)
            f.write(contents.encode('utf-8'))

    def compress(self, contents):
        compress_bin = getattr(settings, 'STATICFILESPLUS_JS_COMPRESS_BIN', 'uglifyjs')
        compress_args = getattr(settings, 'STATICFILESPLUS_JS_COMPRESS_ARGS',
                ['-', '--mangle', '--compress'])
        cmd_args = [compress_bin] + compress_args
        if 'uglifyjs' in compress_bin:
            hint = "Have you installed UglifyJS? See https://github.com/mishoo/UglifyJS2"
        else:
            hint = ''
        return call_command(cmd_args, input=contents.encode('utf8'), hint=hint).decode('utf8')
