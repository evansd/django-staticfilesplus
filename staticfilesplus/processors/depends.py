import os

from .base import BaseProcessor
from .depends import DirectiveProcessor


class BaseDependsProcessor(BaseProcessor):

    extension = None
    supports_source_maps = True

    def __init__(self, *args, **kwargs):
        super(BaseDependsProcessor, self).__init__(*args, **kwargs)
        self.input_extension = self.extension
        self.output_extension = self.extension
        self.url_prefix = getattr(self.settings, 'STATIC_URL', '/')

    def process(self, input_name, input_path, outputs):
        with DirectiveProcessor(input_path, load_path=self.load_paths) as f:
            file_list = f.file_list
            if len(file_list) == 1:
                return self.original_files(input_name, input_path)
            last_output_path = outputs[-1][1]
            if not self.any_files_modified_since(last_output_path, file_list):
                return outputs
            output_path = outputs[0][1]
            if self.source_maps_enabled:
                source_map_name, source_map_path = outputs[1]
                with self.create(output_path) as h:
                    source_map = f.write_with_source_map(h,
                            source_map_name=os.path.basename(source_map_name),
                            prefix=self.url_prefix)
                with self.create(source_map_path) as h:
                    source_map.dump(h)
            else:
                with self.create(output_path) as h:
                    f.write(h)
            return outputs

    def original_files(self, input_name, input_path):
        if self.source_maps_enabled:
            source_map_name = input_name + '.map'
            source_map_path = input_path + '.map'
            if os.path.exists(source_map_path):
                return [(input_name, input_path), (source_map_name, source_map_path)]
        return [(input_name, input_path)]

    def is_ignored_file(self, name):
        return name.startswith('_') or '/_' in name


class JavaScript(BaseDependsProcessor):
    extension = '.js'

class CSS(BaseDependsProcessor):
    extension = '.css'
