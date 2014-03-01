import contextlib
import errno
import hashlib
import os
import subprocess


class Config(object):

    def get_hash(self):
        digest = hashlib.md5()
        for key, value in sorted(self.__dict__.viewitems()):
            digest.update(key)
            try:
                items = value.viewitems()
                items = sorted(items)
            except AttributeError:
                try:
                    items = value.__iter__()
                except AttributeError:
                    items = (value,)
            for item in items:
                digest.update(str(item))
        return digest.hexdigest()


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
    try:
        proc = subprocess.Popen(*args, **kwargs)
        stdout, stderr = proc.communicate(input)
    except OSError as e:
        if e.errno == errno.ENOENT:
            if hint:
                hint = '\n' + hint
            raise MissingDependency(
                "Couldn't find executable '{executable}'{hint}".format(
                    executable=executable, hint=hint))
        else:
            raise
    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, args[0],
                output=b'\n'.join(filter(None, (stdout, stderr))))
    return stdout


class MissingDependency(Exception):
    pass

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


def any_files_modified_since(output_file, input_files):
    try:
        target_last_modified = os.path.getmtime(output_file)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return True
        raise
    for filename in input_files:
        if os.path.getmtime(filename) > target_last_modified:
            return True
    return False
