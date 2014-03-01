from __future__ import absolute_import, unicode_literals

import errno
import os

from ..lib.directive_processor import DirectiveProcessor
from ..utils import create
from .base import BaseProcessor


class JavaScriptProcessor(BaseProcessor):

    def __init__(self, *args, **kwargs):
        super(JavaScriptProcessor, self).__init__(*args, **kwargs)
        self.source_maps = getattr(self.settings,
                'STATICFILESPLUS_SOURCE_MAPS', self.settings.DEBUG)

    def reverse_mapping(self, name):
        if name.endswith('.js.map'):
            return name[:-len('.map')]

    def process_file(self, input_name, input_path):
        if input_name.endswith('.js.map'):
            return []
        if not input_name.endswith('.js'):
            return None
        if self.is_ignored_file(input_name):
            return []
        output_name = input_name
        source_map_name = output_name + '.map'
        output_path = self.get_path(output_name)
        source_map_path = self.get_path(source_map_name)
        if self.source_maps:
            outputs = [(output_name, output_path), (source_map_name, source_map_path)]
        else:
            outputs = [(output_name, output_path)]
        processed_file = DirectiveProcessor(input_path,
                load_paths=self.load_paths)
        if self.files_not_modified_since(output_path, processed_file.file_list):
            processed_file.close()
            return outputs
        if not self.source_maps:
            with create(output_path) as f:
                processed_file.write(f)
        else:
            with create(output_path) as f:
                source_map = processed_file.write_with_source_map(f,
                        source_map_name=os.path.basename(source_map_name),
                        prefix=self.settings.STATIC_URL)
            with create(source_map_path) as f:
                source_map.dump(f)
        return outputs

    def is_ignored_file(self, name):
        return name.startswith('_') or '/_' in name

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
