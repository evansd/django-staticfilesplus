from __future__ import absolute_import, unicode_literals

import errno
import os

from django.conf import settings

from ..lib.directive_processor import DirectiveProcessor
from ..utils import get_staticfiles_dirs, call_command, create, Config


class JavaScriptProcessor(object):

    def reverse_mapping(self, name):
        if name.endswith('.js.map'):
            return name[:-len('.map')]

    def process_file(self, input_name, input_path, tmp_dir):
        if not input_name.endswith('.js'):
            return None
        if self.is_ignored_file(input_name):
            return []
        cfg = self.get_config(input_name)
        suffix = '.' + cfg.get_hash()
        output_name = input_name
        output_path = os.path.join(tmp_dir, output_name) + suffix
        if cfg.source_maps:
            source_map_name = output_name + '.map'
            source_map_path = os.path.join(tmp_dir, source_map_name) + suffix
            outputs = [(output_name, output_path), (source_map_name, source_map_path)]
        else:
            outputs = [(output_name, output_path)]
        processed_file = DirectiveProcessor(input_path,
                load_paths=get_staticfiles_dirs())
        if self.files_not_modified_since(output_path, processed_file.file_list):
            processed_file.close()
            return outputs
        if not cfg.source_maps:
            with create(output_path) as f:
                processed_file.write(f)
        else:
            with create(output_path) as f:
                source_map = processed_file.write_with_source_map(f,
                        source_map_name=os.path.basename(source_map_name),
                        prefix=settings.STATIC_URL)
            with create(source_map_path) as f:
                source_map.dump(f, inline_sources=(not cfg.compress))
        if cfg.compress:
            compress_bin = getattr(settings, 'STATICFILESPLUS_JS_COMPRESS_BIN', 'uglifyjs')
            args = [compress_bin, output_path, '--output', output_path]
            args.extend(cfg.compress_args)
            if cfg.source_maps:
                args.extend([
                    '--in-source-map', source_map_path,
                    '--source-map', source_map_path,
                    '--source-map-url', os.path.basename(source_map_name),
                ])
                call_command(args,
                        hint="Have you installed UglifyJS? "
                             "See https://github.com/mishoo/UglifyJS2")
            if cfg.source_maps:
                source_map.add_inline_sources(source_map_path)
        return outputs

    def is_ignored_file(self, name):
        return name.startswith('_') or '/_' in name

    def get_config(self, input_name):
        cfg = Config()
        cfg.source_maps = getattr(settings,
                'STATICFILESPLUS_SOURCE_MAPS', settings.DEBUG)
        cfg.compress = getattr(settings,
                'STATICFILESPUS_JS_COMPRESS', not settings.DEBUG)
        cfg.compress_args = getattr(settings,
                'STATICFILESPUS_UGLIFY_ARGS', ('--mangle', '--compress'))
        return cfg

    def files_not_modified_since(self, output_file, input_files):
        try:
            target_last_modified = os.path.getmtime(output_file)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        for filename in input_files:
            if os.path.getmtime(filename) > target_last_modified:
                return False
        return True

