import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.finders import (get_finders,
        FileSystemFinder as DjangoFileSystemFinder,
        AppDirectoriesFinder as DjangoAppDirectoriesFinder)
from django.core.urlresolvers import get_callable


from . import ProcessorNotUsed


def get_staticfiles_dirs():
    """
    Return list of all staticfiles directories
    """
    dirs = []
    for finder in get_finders():
        if isinstance(finder, (DjangoAppDirectoriesFinder, DjangoFileSystemFinder)):
            for storage in finder.storages.values():
                dirs.append(storage.location)
    return dirs


class ArbitraryFileStorage(FileSystemStorage):
    """
    Storage backend which allows an arbitrary mapping of names to paths
    """
    def __init__(self):
        self.base_location = None
        self.location = None
        self.base_url = None
        self.file_map = {}

    def path(self, name):
        return self.file_map[name]

    def add_file(self, name, path):
        self.file_map[name] = path


class ProcessorMixin(object):
    """
    Adds pre-processor support to a StaticFilesFinder
    """
    def __init__(self, *args, **kwargs):
        super(ProcessorMixin, self).__init__(*args, **kwargs)
        self.tmp_dir = getattr(settings, 'STATICFILESPLUS_TMP_DIR',
                          os.path.join(settings.STATIC_ROOT, 'staticfilesplus_tmp'))
        setting_name = 'STATICFILESPLUS_PROCESSORS'
        self.processor_names = getattr(settings, setting_name, [])
        if not isinstance(self.processor_names, (list, tuple)):
            raise ImproperlyConfigured(
                "Your {} setting is not a tuple or list; perhaps you "
                "forgot a trailing comma?".format(setting_name))

    @property
    def processors(self):
        # This list needs to initialized lazily on first access, rather than as
        # part of __init__ because we can't call `get_staticfiles_dirs` during
        # __init__ without circularity
        try:
            return self._processors
        except AttributeError:
            pass
        load_paths = get_staticfiles_dirs()
        processors = []
        for processor_name in self.processor_names:
            Processor = get_callable(processor_name)
            try:
                processor = Processor(
                    self.tmp_dir,
                    settings=settings,
                    load_paths=load_paths)
            except ProcessorNotUsed:
                continue
            processors.append(processor)
        self._processors = processors
        return processors

    def find(self, original_name, all=False):
        for name, path in self.candidate_files(original_name):
            outputs = self.process_file(name, path)
            for output_name, output_path in outputs:
                if output_name == original_name:
                    return output_path
        return []

    def candidate_files(self, original_name):
        names = [processor.reverse_mapping(original_name)
                    for processor in self.processors]
        names.append(original_name)
        seen = set()
        for name in names:
            if name is not None and name not in seen:
                seen.add(name)
                path = super(ProcessorMixin, self).find(name)
                if path:
                    yield name, path

    def process_file(self, name, path):
        files = [(name, path)]
        for processor in self.processors:
            new_files = []
            for next_file in files:
                processed = processor.process_file(next_file[0], next_file[1])
                new_files.extend(processed if processed is not None else [next_file])
            files = new_files
        return files

    def list(self, *args, **kwargs):
        output_storage = ArbitraryFileStorage()
        for name, storage in super(ProcessorMixin, self).list(*args, **kwargs):
            # Prefix the relative path if the source storage contains it
            if getattr(storage, 'prefix', None):
                full_name = os.path.join(storage.prefix, name)
            else:
                full_name = name
            path = storage.path(full_name)
            outputs = self.process_file(full_name, path)
            for output_name, output_path in outputs:
                if output_name == full_name and output_path == path:
                    yield name, storage
                else:
                    output_storage.add_file(output_name, output_path)
                    yield output_name, output_storage


class FileSystemFinder(ProcessorMixin, DjangoFileSystemFinder):
    pass

class AppDirectoriesFinder(ProcessorMixin, DjangoAppDirectoriesFinder):
    pass
