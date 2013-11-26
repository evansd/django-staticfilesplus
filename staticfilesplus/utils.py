import contextlib
import errno
import os
import subprocess

from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.finders import (get_finders,
        AppDirectoriesFinder, FileSystemFinder)


@contextlib.contextmanager
def create(filename):
    """
    Opens `filename` for writing, creating any necessary
    parent directories
    """
    try:
        with open(filename, 'wb') as handle:
            yield handle
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        make_directories(filename)
        with open(filename, 'wb') as handle:
            yield handle

def make_directories(filename):
    path = os.path.dirname(filename)
    try:
        os.makedirs(path, 0o775)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def get_staticfiles_dirs():
    dirs = []
    for finder in get_finders():
        if isinstance(finder, (AppDirectoriesFinder, FileSystemFinder)):
            for storage in finder.storages.values():
                dirs.append(storage.location)
    return dirs


def call_command(*args, **kwargs):
    """
    Wraps subprocess.Popen to produce slightly more readable
    and informative error output
    """
    executable = args[0][0]
    hint = kwargs.pop('hint', '')
    input = kwargs.pop('input', None)
    for key in ('stdin', 'stdout', 'stderr'):
        kwargs.setdefault(key, subprocess.PIPE)
    proc = subprocess.Popen(*args, **kwargs)
    try:
        stdout, stderr = proc.communicate(input)
    except OSError as e:
        if e.errno == errno.ENOENT:
            if hint:
                hint = '\n' + hint
            raise ImproperlyConfigured(
                "Couldn't find executable '{executable}'{hint}".format(
                    executable=executable, hint=hint))
        else:
            raise
    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, args[0],
                output=b'\n'.join(filter(None, (stdout, stderr))))
    return stdout


class CalledProcessError(subprocess.CalledProcessError):
    """
    Wraps subprocess.CalledProcessError to produce slightly more readable
    and informative error output
    """

    def __str__(self):
        return '\n' \
               'command: {command}\n' \
               'exit status: {returncode}\n' \
               'output:\n{output}'.format(
                    command=' '.join(self.cmd),
                    returncode=self.returncode,
                    output=self.output.decode('utf8'))


def any_files_modified_since(target_file, directories, extension):
    """
    Checks whether any files in `directories` matching `extension`
    have been modified since `target_file` was last modified
    """
    try:
        target_last_modified = os.path.getmtime(target_file)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return True
        raise
    for directory in directories:
        for root, _, files in os.walk(directory):
            for filename in files:
                if not filename.endswith(extension):
                    continue
                last_modified = os.path.getmtime(os.path.join(root, filename))
                if last_modified > target_last_modified:
                    return True
    return False
