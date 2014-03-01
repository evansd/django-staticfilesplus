from __future__ import absolute_import, unicode_literals

import os

from . import BaseProcessor


class SassProcessor(BaseProcessor):
    input_extension = '.sass'
    output_extension = '.css'
    supports_source_maps = False

    def __init__(self, *args, **kwargs):
        super(SassProcessor, self).__init__(*args, **kwargs)
        self.sass_bin = getattr(self.settings, 'STATICFILESPLUS_SASS_BIN', 'sass')

    def process(self, input_name, input_path, outputs):
        output_path = outputs[0][1]
        extra_args = ['--style', 'compressed'] if self.minify_enabled else []
        load_path = os.pathsep.join(self.load_paths)
        self.call_command([self.sass_bin, '--load-path', load_path]
                + extra_args + ['--update', input_path + ':' + output_path],
            hint="Have you installed Sass? See http://sass-lang.com")
        return outputs

    def is_ignored_file(self, name):
        return any(part.startswith('_') for part in name.split(os.sep))


class ScssProcessor(SassProcessor):
    input_extension = '.scss'
