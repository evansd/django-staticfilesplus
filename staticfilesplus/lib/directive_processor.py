"""
Implementation of a minimal subset of the Directive Processor from Rails' Sprockets
library. See: https://github.com/sstephenson/sprockets/#the-directive-processor

Implements just the `require` and `stub` directives.

Thanks to Sam Stephenson (author of Sprockets), and to Mike Yumatov (author of Gears
-- https://github.com/gears/gears) for inspiration.
"""
import re
import os
import shlex
import sys


class DirectiveProcessor(object):

    class DirectiveError(Exception):
        pass

    HEADER_RE = re.compile(r"""
        ^( \s* (
            ( /\* .*? \*/ ) |  # multiline comment
            ( // [^\n]* )+ |   # slash comment
            ( \# [^\n]* )+     # dash comment
        ) )+
        """,
        re.DOTALL | re.VERBOSE)

    DIRECTIVE_RE = re.compile(r"""
        ^ \s* (?:\*|//|\#) \s* = \s* ( \w+ [./'"\s\w-]* ) $
        """,
        re.VERBOSE)

    current_line = None
    current_file = None

    def __init__(self, load_paths=None):
        self.load_paths = load_paths if load_paths is not None else []

    def load(self, name):
        return self.process_file(name, path_context=os.getcwd(), files_seen=set())[0]

    def process_file(self, name, path_context, files_seen):
        path = self.find_path(name, path_context)
        if path in files_seen:
            return None, files_seen
        files_seen.add(path)
        source = self.get_file_contents(path)
        self.current_file = path
        directives, body = self.extract_directives(source)
        output = []
        for line_num, directive, arg in directives:
            # Keep track of line number for more helpful exceptions
            self.current_line = line_num
            self.current_file = path
            content, new_files_seen = self.process_directive(
                    directive, arg, path_context=path, files_seen=files_seen)
            self.current_line = None
            files_seen.update(new_files_seen)
            if content is not None:
                output.append(content)
        output.append(body)
        return '\n'.join(output), files_seen

    def get_file_contents(self, path):
        with open(path, 'rb') as f:
            return f.read().decode('utf-8')

    def process_directive(self, directive, arg, path_context, files_seen):
        if directive not in ('require', 'stub'):
            raise self.error('Unimplemented directive: {}'.format(directive))
        output, files_seen = self.process_file(arg, path_context, files_seen)
        if directive == 'require':
            return output, files_seen
        else:
            return None, files_seen

    def find_path(self, name, path_context):
        options = self.find_path_options(name, path_context)
        for option in options:
            if os.path.exists(option):
                return option
        raise self.error('Unable to find "{}", tried:\n  {}'.format(
                name, '\n  '.join(options)))

    def find_path_options(self, name, path_context):
        """
        Given a filename and a path context in which to resolve relative
        paths, return a list of possible locations for the file
        """
        # If the name doesn't have the extension then we need to try
        # both with and without the extension
        extension = os.path.splitext(path_context)[1]
        if not name.endswith(extension):
            with_extension = lambda path: [path, path + extension]
        else:
            with_extension = lambda path: [path]
        # Absolute paths are straightforward
        if os.path.isabs(name):
            return with_extension(name)
        # Relative paths get resolved with respect to path_context
        if name.startswith('./') or name.startswith('../'):
            dir_context = os.path.dirname(path_context)
            path = os.path.normpath(os.path.join(dir_context, name))
            return with_extension(path)
        # Otherwise we walk over the load_paths
        paths = []
        for load_path in self.load_paths:
            path = os.path.join(load_path, name)
            paths.extend(with_extension(path))
        return paths

    def extract_directives(self, source):
        match = self.HEADER_RE.match(source)
        if not match:
            header, rest_of_body = '', source
        else:
            header = match.group(0)
            rest_of_body = source[len(header):]
        directives = []
        body = []
        for line_num, line in enumerate(header.splitlines(), start=1):
            match = self.DIRECTIVE_RE.match(line)
            if match:
                # Keep track of line number for more helpful exceptions
                self.current_line = line_num
                directive = self.parse_directive(match.group(1))
                self.current_line = None
                directives.append((line_num,) + directive)
            else:
                body.append(line)
        body.append(rest_of_body.strip('\n'))
        return directives, '\n'.join(body)

    def parse_directive(self, directive):
        # shlex didn't support Unicode prior to 2.7.3
        if sys.version_info < (2, 7, 3):
            directive = directive.encode('utf-8')
        try:
            args = tuple(shlex.split(directive))
        except ValueError as e:
            raise self.error(str(e))
        if len(args) != 2:
            raise self.error('Expected 2 arguments but got {} in: {}'.format(
                len(args), directive))
        return args

    def error(self, msg):
        """
        Raise a DirectiveError with the current file and line as context
        """
        if self.current_line and self.current_file:
            msg = '{}\nError in {} line {}'.format(
                    msg, self.current_file, self.current_line)
        return self.DirectiveError(msg)



