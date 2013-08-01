import errno
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
        tmp_dir = getattr(settings, 'STATICFILESPLUS_TMP_DIR',
                          os.path.join(settings.STATIC_ROOT, 'staticfilesplus_tmp'))
        self.tmp_storage = FileSystemStorage(location=tmp_dir)
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

    def find(self, path, all=False):
        if all:
            raise NotImplementedError("Staticfilesplus can't handle the `all` flag at the moment")
        # Walk the list of processors, seeing if any want to handle
        # this request and if there's a matching file
        tried_names = set()
        for processor in self.processors:
            orig_name = processor.get_original_name(path)
            if orig_name is None or orig_name in tried_names:
                continue
            tried_names.add(orig_name)
            match = super(ProcessorMixin, self).find(orig_name)
            if match:
                if processor.is_ignored_file(orig_name):
                    return []
                else:
                    return self.process_file(processor, match, path)
        # As a last resort we try the untransformed path
        if path not in tried_names:
            return super(ProcessorMixin, self).find(path)
        else:
            return []

    def list(self, *args, **kwargs):
        for name, storage in super(ProcessorMixin, self).list(*args, **kwargs):
            # Walk the list of processors, seeing if any want to handle
            # this type of file
            matched_processor = None
            for processor in self.processors:
                processed_name = processor.get_processed_name(name)
                if processed_name is not None:
                    matched_processor = processor
                    break
            if matched_processor is None:
                yield name, storage
            else:
                # If the processor explicitly excludes this file then pretend
                # we never found it
                if matched_processor.is_ignored_file(name):
                    continue
                path = storage.path(name)
                self.process_file(matched_processor, path, processed_name)
                yield processed_name, self.tmp_storage

    def process_file(self, processor, path, processed_name):
        # Get the full output path
        output_path = self.tmp_storage.path(processed_name)
        # Create the required directories
        try:
            os.makedirs(os.path.dirname(output_path), 0o775)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        # Process the file
        processor.process_file(path, output_path)
        return output_path


class FileSystemFinder(ProcessorMixin, DjangoFileSystemFinder):
    pass

class AppDirectoriesFinder(ProcessorMixin, DjangoAppDirectoriesFinder):
    pass
