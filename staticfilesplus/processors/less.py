from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings

from . import BaseProcessor
from ..utils import call_command, get_staticfiles_dirs, any_files_modified_since


class LESSProcessor(BaseProcessor):
    original_suffix = '.less'
    processed_suffix = '.css'

    def is_ignored_file(self, path):
        return any(part.startswith('_') for part in path.split(os.sep))

    def process_file(self, input_path, output_path):
        staticfiles_dirs = get_staticfiles_dirs()
        # Bail early if no LESS files have changed since we last processed
        # this file
        if settings.DEBUG and not any_files_modified_since(output_path,
                directories=staticfiles_dirs,
                extension=self.original_suffix):
            return
        compress = getattr(settings, 'STATICFILESPLUS_LESS_COMPRESS',
                not settings.DEBUG)
        less_bin = getattr(settings, 'STATICFILESPLUS_LESS_BIN', 'lessc')
        extra_args = ['--compress'] if compress else []
        include_path = os.pathsep.join(staticfiles_dirs)
        call_command([less_bin, '--include-path={}'.format(include_path)]
                    + extra_args + [input_path, output_path],
               hint="Have you installed LESS? See http://lesscss.org")
