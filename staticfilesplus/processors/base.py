import os

from .. import ProcessorNotUsed
from ..utils import call_command, make_directories, create, any_files_modified_since

__all__ = ['ProcessorInterface', 'BaseProcessor', 'ProcessorNotUsed']


class EmptySettings(object):
    DEBUG = True


class ProcessorInterface(object):
    """
    The minimum a processor class needs to implement
    """

    def __init__(self, tmp_dir, settings=EmptySettings(), load_paths=()):
        self.tmp_dir = tmp_dir
        self.settings = settings
        self.load_paths = load_paths

    def reverse_mapping(self, name):
        return None

    def process_file(self, input_name, input_path):
        raise NotImplementedError()


class BaseProcessor(ProcessorInterface):

    input_extension = None
    output_extension = None
    supports_source_maps = False

    def __init__(self, *args, **kwargs):
        super(BaseProcessor, self).__init__(*args, **kwargs)
        self.minify_enabled = getattr(self.settings,
                'STATICFILESPLUS_MINIFY', not self.settings.DEBUG)
        self.source_maps_enabled = getattr(self.settings,
                'STATICFILESPLUS_SOURCE_MAPS', self.settings.DEBUG)

    def reverse_mapping(self, name):
        if self.supports_source_maps:
            if name.endswith(self.output_extension + '.map'):
                return name[:-len(self.output_extension + '.map')] + self.input_extension
        if self.output_extension != self.input_extension:
            if name.endswith(self.output_extension):
                return name[:-len(self.output_extension)] + self.input_extension

    def process_file(self, input_name, input_path):
        if self.supports_source_maps:
            if input_name.endswith(self.input_extension + '.map'):
                return []
        if not input_name.endswith(self.input_extension):
            return None
        if self.is_ignored_file(input_name):
            return []
        output_name = input_name[:-len(self.input_extension)] + self.output_extension
        output_path = self.get_path(output_name)
        outputs = [(output_name, output_path)]
        if self.supports_source_maps and self.source_maps_enabled:
            source_map_name = output_name + '.map'
            source_map_path = self.get_path(source_map_name)
            outputs.append((source_map_name, source_map_path))
        return self.process(input_name, input_path, outputs)

    def process(self, input_name, input_path, outputs):
        raise NotImplementedError()

    def is_ignored_file(self, name):
        return False

    def get_path(self, name):
        return os.path.join(self.tmp_dir, self.__class__.__name__, name)

    # Attach utility functions as static methods
    create = staticmethod(create)
    make_directories = staticmethod(make_directories)
    call_command = staticmethod(call_command)
    any_files_modified_since = staticmethod(any_files_modified_since)
