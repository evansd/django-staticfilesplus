from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings

from ..utils import (call_command, get_staticfiles_dirs, any_files_modified_since,
        make_directories)


class LESSProcessor(object):

    def reverse_mapping(self, name):
        if name.endswith('.css'):
            return name[:-len('.css')] + '.less'
        if name.endswith('.css.map'):
            return name[:-len('.css.map')] + '.less'

    def process_file(self, input_name, input_path, output_dir):
        if not input_name.endswith('.less'):
            return None
        if input_name.startswith('_') or '/_' in input_name:
            return []
        css_name = input_name[:-len('.less')] + '.css'
        outputs = [css_name, css_name + '.map']
        staticfiles_dirs = get_staticfiles_dirs()
        # Bail early if no LESS files have changed since we last processed
        # this file
        output_path = os.path.join(output_dir, css_name)
        if settings.DEBUG and not any_files_modified_since(output_path,
                directories=staticfiles_dirs,
                extension='.less'):
            return outputs
        make_directories(output_path)
        compress = getattr(settings, 'STATICFILESPLUS_LESS_COMPRESS',
                not settings.DEBUG)
        less_bin = getattr(settings, 'STATICFILESPLUS_LESS_BIN', 'lessc')
        extra_args = ['--compress'] if compress else []
        extra_args.extend(['--source-map', '--source-map-less-inline'])
        include_path = os.pathsep.join(staticfiles_dirs)
        call_command([less_bin, '--include-path={}'.format(include_path)]
                    + extra_args + [input_path, output_path],
               hint="Have you installed LESS? See http://lesscss.org")
        return outputs
