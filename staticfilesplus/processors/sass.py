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
        extra_args = ['--style', 'compressed'] if compress else []
        load_path = os.pathsep.join(get_staticfiles_dirs())
        call_command([sass_bin, '--load-path', load_path]
                + extra_args + ['--update', input_path + ':' + output_path],
            hint="Have you installed Sass? See http://sass-lang.com")


class ScssProcessor(SassProcessor):
    original_suffix = '.scss'
