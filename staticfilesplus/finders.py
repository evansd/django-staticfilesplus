import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.finders import (
        FileSystemFinder as DjangoFileSystemFinder,
        AppDirectoriesFinder as DjangoAppDirectoriesFinder)
from django.core.urlresolvers import get_callable


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
        # Configure processors
        if not isinstance(settings.STATICFILESPLUS_PROCESSORS, (list, tuple)):
            raise ImproperlyConfigured(
                "Your STATICFILESPLUS_PROCESSORS setting is not a tuple or list; "
                "perhaps you forgot a trailing comma?")
        self.processors = []
        for processor in settings.STATICFILESPLUS_PROCESSORS:
            Processor = get_callable(processor)
            self.processors.append(Processor())

    def find(self, original_name, all=False):
        if all:
            raise NotImplementedError(
                    "Staticfilesplus can't handle the `all` flag at the moment")
        for name, path in self.candidate_files(original_name):
            outputs = self.process_file(name, path)
            if outputs is not None:
                for output_name, output_path in outputs:
                    if output_name == original_name:
                        return output_path
            elif name == original_name:
                return path
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
        for processor in self.processors:
            outputs = processor.process_file(name, path, self.tmp_dir)
            if outputs is not None:
                return outputs
        return None

    def list(self, *args, **kwargs):
        output_storage = ArbitraryFileStorage()
        for name, storage in super(ProcessorMixin, self).list(*args, **kwargs):
            path = storage.path(name)
            outputs = self.process_file(name, path)
            if outputs is not None:
                for output_name, output_path in outputs:
                    output_storage.add_file(output_name, output_path)
                    yield output_name, output_storage
            else:
                # If no processor has claimed this file, yield the original
                # values
                yield name, storage


class FileSystemFinder(ProcessorMixin, DjangoFileSystemFinder):
    pass

class AppDirectoriesFinder(ProcessorMixin, DjangoAppDirectoriesFinder):
    pass
