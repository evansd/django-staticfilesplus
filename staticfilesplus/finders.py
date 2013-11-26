import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.finders import (
        FileSystemFinder as DjangoFileSystemFinder,
        AppDirectoriesFinder as DjangoAppDirectoriesFinder)
from django.core.urlresolvers import get_callable


class ProcessorMixin(object):
    """
    Adds pre-processor support to a StaticFilesFinder
    """

    def __init__(self, *args, **kwargs):
        super(ProcessorMixin, self).__init__(*args, **kwargs)
        # Configure temporary storage space for processed files
        self.tmp_dir = getattr(settings, 'STATICFILESPLUS_TMP_DIR',
                          os.path.join(settings.STATIC_ROOT, 'staticfilesplus_tmp'))
        self.tmp_storage = FileSystemStorage(location=self.tmp_dir)
        # Can't set this as None through the constructor because it will
        # default to MEDIA_URL
        self.tmp_storage.base_url = None
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
        for name in self.candidate_names(original_name):
            path = super(ProcessorMixin, self).find(name)
            if path:
                break
        else:
            return []
        for processor in self.processors:
            outputs = processor.process_file(name, path, self.tmp_dir)
            if outputs is not None:
                if original_name in outputs:
                    return os.path.join(self.tmp_dir, original_name)
                else:
                    return []
        else:
            return path

    def candidate_names(self, original_name):
        for processor in self.processors:
            name = processor.reverse_mapping(original_name)
            if name is not None:
                yield name
        yield original_name

    def list(self, *args, **kwargs):
        for name, storage in super(ProcessorMixin, self).list(*args, **kwargs):
            path = storage.path(name)
            for processor in self.processors:
                outputs = processor.process_file(
                        name, path, self.tmp_dir)
                if outputs is not None:
                    for output_name in outputs:
                        yield output_name, self.tmp_storage
                    break
            else:
                yield name, storage


class FileSystemFinder(ProcessorMixin, DjangoFileSystemFinder):
    pass

class AppDirectoriesFinder(ProcessorMixin, DjangoAppDirectoriesFinder):
    pass
