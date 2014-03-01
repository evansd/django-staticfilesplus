import os

from ..source_maps import copy_sources_inline, copy_single_source_inline
from .base import BaseProcessor, ProcessorNotUsed


class UglifyJSProcessor(BaseProcessor):

    input_extension = '.js'
    output_extension = '.js'
    supports_source_maps = True

    def __init__(self, *args, **kwargs):
        super(UglifyJSProcessor, self).__init__(*args, **kwargs)
        if not self.minify_enabled:
            raise ProcessorNotUsed()
        self.uglify_bin = getattr(self.settings,
                'STATICFILESPLUS_UGLIFYJS_BIN', 'uglifyjs')

    def process(self, input_name, input_path, outputs):
        last_output_path = outputs[-1][1]
        if not self.any_files_modified_since(last_output_path, [input_path]):
            return outputs
        output_path = outputs[0][1]
        self.make_directories(output_path)
        in_source_map = input_path + '.map'
        if not os.path.exists(in_source_map):
            in_source_map = None
        args = [self.uglify_bin, input_path, '--output', output_path]
        args.extend(('--mangle', '--compress'))
        if self.source_maps_enabled:
            source_map_name, source_map_path = outputs[1]
            if in_source_map is not None:
                args.extend([
                    '--in-source-map', in_source_map])
            args.extend([
                '--source-map', source_map_path,
                '--source-map-url', os.path.basename(source_map_name),
            ])
        self.call_command(args,
                hint="Have you installed UglifyJS? "
                     "See https://github.com/mishoo/UglifyJS2")
        if self.source_maps_enabled:
            if in_source_map is not None:
                copy_sources_inline(source_map_path, in_source_map)
            else:
                copy_single_source_inline(source_map_path, input_path)
        return outputs
