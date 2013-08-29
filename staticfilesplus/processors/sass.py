from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings

from . import BaseProcessor
from ..utils import get_staticfiles_dirs, call_command


class SassProcessor(BaseProcessor):
    original_suffix = '.sass'
    processed_suffix = '.css'

    def is_ignored_file(self, path):
        return any(part.startswith('_') for part in path.split(os.sep))

    def process_file(self, input_path, output_path):
        compress = getattr(settings, 'STATICFILESPLUS_SASS_COMPRESS',
                not settings.DEBUG)
        sass_bin = getattr(settings, 'STATICFILESPLUS_SASS_BIN', 'sass')
        if compress:
            extra_args = ['--style', 'compressed']
        else:
            extra_args = []
        call_command([sass_bin, '--load-path', self.get_load_path()]
                + extra_args + ['--update', input_path + ':' + output_path],
            hint="Have you installed Sass? See http://sass-lang.com")

    def get_load_path(self):
        try:
            return self._load_path
        except AttributeError:
            pass
        dirs = get_staticfiles_dirs()
        self._load_path = os.pathsep.join(dirs)
        return self._load_path


class ScssProcessor(SassProcessor):
    original_suffix = '.scss'
