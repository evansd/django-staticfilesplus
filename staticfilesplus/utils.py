import errno
import subprocess

from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.finders import (get_finders,
        AppDirectoriesFinder, FileSystemFinder)


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

