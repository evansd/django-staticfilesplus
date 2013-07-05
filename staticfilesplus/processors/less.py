from __future__ import absolute_import, unicode_literals

import errno
import os
import subprocess

from django.conf import settings

from . import BaseProcessor


class LESSProcessor(BaseProcessor):
    original_suffix = '.less'
    processed_suffix = '.css'

    def is_ignored_file(self, path):
        return any(part.startswith('_') for part in path.split(os.sep))

    def process_file(self, input_path, output_path):
        compress = getattr(settings, 'STATICFILESPLUS_LESS_COMPRESS',
                not settings.DEBUG)
        extra_args = ['--compress'] if compress else []
        try:
            subprocess.check_call(['lessc'] + extra_args + [input_path, output_path])
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise ValueError('You need to install LESS, see http://lesscss.org')
            else:
                raise
