import errno
import os
import json


from django.conf import settings
from django.contrib.staticfiles.storage import (CachedFilesMixin,
        StaticFilesStorage)


class CachedFilesPlusMixin(CachedFilesMixin):
    """
    Use a simple manifest.json file for storing the mapping of original
    asset filenames to their hash-keyed versions.

    Also provides an option to remove the original unversioned files.
    """
    remove_unversioned = True

    def __init__(self, *args, **kwargs):
        self.remove_unversioned = kwargs.pop('remove_unversioned',
                self.remove_unversioned)
        super(CachedFilesPlusMixin, self).__init__(*args, **kwargs)
        manifest_file = getattr(settings, 'STATICFILESPLUS_MANIFEST',
                os.path.join(settings.STATIC_ROOT, 'static_manifest.json'))
        self.cache = JSONFileCache(manifest_file)

    def cache_key(self, name):
        # Because we're using our own cache backend there's no point doing
        # anything fancy with the cache keys. This also has the advantage
        # that the manifest file is easily readable by humans and other
        # applications if necessary
        return name

    def post_process(self, *args, **kwargs):
        """
        Wrap the original post_process method and delete the unversioned files
        if that option is enabled
        """
        files = super(CachedFilesPlusMixin, self).post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            if self.remove_unversioned and processed:
                self.delete(name)
            yield name, hashed_name, processed


class CachedStaticFilesPlusStorage(CachedFilesPlusMixin, StaticFilesStorage):
    """
    A static file system storage backend which also saves
    hashed copies of the files it saves.
    """
    pass


class JSONFileCache(object):
    """
    A very simple cache backend which stores its contents in a JSON
    file. Designed to be used with the staticfiles contrib app.

    Deliberately doesn't extend BaseCache, or implement the full cache
    API, so you aren't tempted to use it for anything else!
    """

    def __init__(self, cache_file):
        self.cache_file = cache_file
        try:
            # Load the cache file, if it exists
            with open(self.cache_file, 'rb') as f:
                self.cache_dict = json.load(f)
        except IOError as e:
            # If it doesn't exist, set an empty cache
            # (All other errors should be raised)
            if e.errno == errno.ENOENT:
                self.cache_dict = {}
            else:
                raise
        # Wire up the get method directly to the dict
        # getter
        self.get = self.cache_dict.get

    def set(self, key, value, timeout=None):
        self.cache_dict[key] = value

    def set_many(self, values, timeout=None):
        self.cache_dict.update(values)
        # This isn't an atomic update, but given the
        # contrib.staticfiles use case this doesn't
        # matter
        with open(self.cache_file, 'wb') as f:
            json.dump(self.cache_dict, f, indent=2)
