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
        # Walk the list of processors, seeing if any want to handle
        # this request
        matched_processor = None
        for processor in self.processors:
            orig_name = processor.get_original_name(path)
            if orig_name is not None:
                matched_processor = processor
                break
        # We can't handle the `all` flag at the moment
        if not matched_processor or all:
            return super(ProcessorMixin, self).find(path, all=all)
        else:
            # If the processor explicitly excludes this file then pretend
            # we've found nothing
            if matched_processor.is_ignored_file(orig_name):
                return []
            # Search for the original file
            match = super(ProcessorMixin, self).find(orig_name)
            # If we don't find a match for our transformed name, fall back
            # to searching for the untouched name
            if not match:
                if path != orig_name:
                    return super(ProcessorMixin, self).find(path)
                else:
                    return match
            # Process the file
            return self.process_file(matched_processor, match, path)

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
