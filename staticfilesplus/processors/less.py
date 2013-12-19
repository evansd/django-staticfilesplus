from __future__ import absolute_import, unicode_literals

import os

from django.conf import settings

from ..utils import (call_command, get_staticfiles_dirs, any_files_modified_since,
        make_directories, Config)


class LESSProcessor(object):

    def reverse_mapping(self, name):
        if name.endswith('.css'):
            return name[:-len('.css')] + '.less'
        if name.endswith('.css.map'):
            return name[:-len('.css.map')] + '.less'

    def process_file(self, input_name, input_path, tmp_dir):
        if not input_name.endswith('.less'):
            return None
        if self.is_ignored_file(input_name):
            return []
        cfg = self.get_config(input_name)
        output_name = input_name[:-len('.less')] + '.css'
        output_path = os.path.join(tmp_dir, cfg.get_hash(), output_name)
        if cfg.source_maps:
            outputs = [(output_name, output_path), (output_name + '.map', output_path + '.map')]
        else:
            outputs = [(output_name, output_path)]
        staticfiles_dirs = get_staticfiles_dirs()
        # Bail early if no LESS files have changed since we last processed
        # this file
        if not any_files_modified_since(output_path,
                directories=staticfiles_dirs,
                extension='.less'):
            return outputs
        make_directories(output_path)
        less_bin = getattr(settings, 'STATICFILESPLUS_LESS_BIN', 'lessc')
        include_path = os.pathsep.join(staticfiles_dirs)
        args = [less_bin, '--include-path={}'.format(include_path)]
        if cfg.source_maps:
            args.extend(['--source-map', '--source-map-less-inline'])
        if cfg.compress:
            args.append('--clean-css')
        args.extend([input_path, output_path])
        call_command(args, hint="Have you installed LESS? See http://lesscss.org")
        return outputs

    def is_ignored_file(self, name):
        return name.startswith('_') or '/_' in name

    def get_config(self, input_name):
        cfg = Config()
        cfg.source_maps = getattr(settings,
                'STATICFILESPLUS_SOURCE_MAPS', settings.DEBUG)
        cfg.compress = getattr(settings,
                'STATICFILESPLUS_LESS_COMPRESS', not settings.DEBUG)
        return cfg
