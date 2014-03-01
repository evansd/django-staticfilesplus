from __future__ import absolute_import, unicode_literals

import os

from .base import BaseProcessor


class LESSProcessor(BaseProcessor):

    input_extension = '.less'
    output_extension = '.css'
    supports_source_maps = True

    def __init__(self, *args, **kwargs):
        super(LESSProcessor, self).__init__(*args, **kwargs)
        self.less_bin = getattr(self.settings,
                'STATICFILESPLUS_LESS_BIN', 'lessc')

    def process(self, input_name, input_path, outputs):
        # Bail early if no LESS files have changed since we last processed
        # this file
        last_output_path = outputs[-1][1]
        if not self.any_files_modified_since(
                last_output_path,
                self.list_all_input_files()):
            return outputs
        output_path = outputs[0][1]
        self.make_directories(output_path)
        include_path = os.pathsep.join(self.load_paths)
        args = [self.less_bin,
                # Disable colourized output
                '--no-color',
                '--include-path={}'.format(include_path)]
        if self.source_maps_enabled:
            args.extend(['--source-map', '--source-map-less-inline'])
        if self.minify_enabled:
            args.append('--compress')
        args.extend([input_path, output_path])
        self.call_command(args, hint="Have you installed LESS? See http://lesscss.org")
        return outputs

    def list_all_input_files(self):
        for directory in self.load_paths:
            for root, _, files in os.walk(directory):
                for filename in files:
                    if filename.endswith(self.input_extension):
                        yield os.path.join(root, filename)

    def is_ignored_file(self, name):
        return name.startswith('_') or '/_' in name
