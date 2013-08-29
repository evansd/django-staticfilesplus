from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings

from . import BaseProcessor
from ..utils import call_command


class LESSProcessor(BaseProcessor):
    original_suffix = '.less'
    processed_suffix = '.css'

    def is_ignored_file(self, path):
        return any(part.startswith('_') for part in path.split(os.sep))

    def process_file(self, input_path, output_path):
        compress = getattr(settings, 'STATICFILESPLUS_LESS_COMPRESS',
                not settings.DEBUG)
        less_bin = getattr(settings, 'STATICFILESPLUS_LESS_BIN', 'lessc')
        extra_args = ['--compress'] if compress else []
        call_command([less_bin] + extra_args + [input_path, output_path],
                hint="Have you installed LESS? See http://lesscss.org")
