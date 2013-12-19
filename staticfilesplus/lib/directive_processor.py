"""
Implementation of a minimal subset of the Directive Processor from Rails' Sprockets
library. See: https://github.com/sstephenson/sprockets/#the-directive-processor

Implements just the `require` and `stub` directives.

Thanks to Sam Stephenson (author of Sprockets), and to Mike Yumatov (author of Gears
-- https://github.com/gears/gears) for inspiration.
"""
import collections
import io
import itertools
import os
import re
import shlex
import sys

try:
    import simplejson as json
except ImportError:
    import json


class DirectiveError(Exception):
    filename = None
    line_num = None

    def __str__(self):
        message = Exception.__str__(self)
        if self.filename is not None:
            return 'in "{}" at line {}: {}'.format(
                    self.filename,
                    self.line_num,
                    message)
        else:
            return message

class FileNotFoundError(DirectiveError):
    pass

class UnknownDirectiveError(DirectiveError):
    pass

Directive = collections.namedtuple('Directive', ['command', 'argument'])


class DirectiveProcessor(object):

    HEADER_LINE_RE = re.compile(r"""
        (
            ( \s+ ) |                               # Blocks of whitespace
            ( // .* $ ) |                           # Double-slash comment (to line end)
            ( \# .* $ ) |                           # Hash comment (to line end)
            ( /\* {any_string_except_star_slash} (  # Multiline comment terminated by ...
                \*/ |                               # ... close marker ...
                (?P<open> $ )                       # ... or end of line
            ))
        # Match any combination of the above blocks until end of the line
        )+ $
        """.format(any_string_except_star_slash=r'([^\*]|\*(?!/))*'),
        re.VERBOSE)

    DIRECTIVE_RE = re.compile(r"""
        ^ \s* (?:\*|//|\#) \s* = \s* ( \w+ [./'"\s\w-]*? ) \n? $
        """,
        re.VERBOSE)

    def __init__(self, name=None, load_paths=None):
        self.load_paths = load_paths if load_paths is not None else []
        self.files_seen = set()
        self.handles = set()
        self.output = self.process_file(name, path_context='/')

    @property
    def file_list(self):
        return [filename for (filename, _) in self.output]

    def write_with_source_map(self, f, source_map_name, prefix='/'):
        source_map = SourceMap()
        for filename, lines in self.output:
            url = self.get_url_for_filename(filename, prefix)
            source_map.set_current_file(url)
            for line in lines:
                source_map.add_line(line)
                f.write(line)
        f.write('//# sourceMappingURL={}\n'.format(source_map_name))
        return source_map

    def get_url_for_filename(self, filename, prefix):
        for path in self.load_paths:
            if filename.startswith(path):
                return prefix + filename[len(path):].lstrip('/')
        return os.path.basename(filename)

    def write(self, f):
        for filename, lines in self.output:
            for line in lines:
                f.write(line)

    def process_file(self, name, path_context):
        path = self.find_file(name, path_context)
        if path in self.files_seen:
            return []
        self.files_seen.add(path)
        output = []
        header_lines = []
        lines = self.get_file_lines(path)
        line_num = 1
        try:
            for line, directive in self.extract_directives(lines):
                header_lines.append(line)
                if directive:
                    directive_output = self.exec_directive(directive, path_context=path)
                    output.extend(directive_output)
                line_num += 1
        except DirectiveError as exc:
            # Mark exceptions with the source file and line number. (Only
            # innermost handler should do this hence the `is None` check)
            if exc.filename is None:
                exc.filename = path
                exc.line_num = line_num
            raise
        output.append((path, itertools.chain(header_lines, lines)))
        return output

    def get_file_lines(self, path):
        with io.open(path, 'rt', encoding='utf-8') as f:
            # Store reference to the handle so we can close the file without
            # consuming the iterator if we decide we don't need it
            self.handles.add(f)
            for line in f:
                # Ensure trailing newline. This will only ever match on the
                # last line of the file
                if line[-1] != '\n':
                    line += '\n'
                yield line
            self.handles.remove(f)

    def close(self):
        """Close any open file handles"""
        for handle in self.handles:
            handle.close()

    def exec_directive(self, directive, path_context):
        if directive.command in ('require', 'stub'):
            output = self.process_file(directive.argument, path_context)
            # The `stub` directive just adds files to the `files_seen` set but
            # doesn't return any output
            return output if directive.command != 'stub' else []
        else:
            raise UnknownDirectiveError('Unknown directive: {}'.format(directive.command))

    def find_file(self, name, path_context):
        options = self.get_path_options(name, path_context)
        for option in options:
            if os.path.exists(option):
                return option
        raise FileNotFoundError(
                'Unable to find "{}", looked in:\n  {}'.format(
                    name, '\n  '.join(options)))

    def get_path_options(self, name, path_context):
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

    @classmethod
    def extract_directives(cls, lines):
        for line, is_header in cls.extract_header(lines):
            directive = cls.parse_directive(line) if is_header else None
            yield line, directive

    @classmethod
    def extract_header(cls, lines):
        comment_open = False
        for line in lines:
            start = 0
            # If we're in the middle of a multiline comment, check for the
            # close comment marker and treat that as the beginning of the
            # string if found
            if comment_open:
                close_marker = line.find('*/')
                if close_marker > -1:
                    start = close_marker + 2
                    comment_open = False
            if not comment_open:
                match = cls.HEADER_LINE_RE.match(line, pos=start)
                if not match:
                    break
                if match.group('open') is not None:
                    comment_open = True
            yield line, True
        else:
            # If we exhausted the iterator without breaking then there are no
            # non-header lines
            return
        # Otherwise the last line processed is the first non-header line
        yield line, False

    @classmethod
    def parse_directive(cls, line):
        match = cls.DIRECTIVE_RE.match(line)
        if not match:
            return None
        # shlex didn't support Unicode prior to 2.7.3
        if sys.version_info < (2, 7, 3):
            text = match.group(1).encode('utf-8')
        else:
            text = match.group(1)
        try:
            args = tuple(shlex.split(text))
        except ValueError as exc:
            raise DirectiveError('{} in: {}'.format(exc, text))
        if len(args) != 2:
            raise DirectiveError('Expected 2 arguments but got {} in {}'.format(
                len(args), text))
        return Directive(command=args[0], argument=args[1])


class SourceMap(object):

    BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    VLQ_BASE_SHIFT = 5
    # binary: 100000
    VLQ_BASE = 1 << VLQ_BASE_SHIFT
    # binary: 011111
    VLQ_BASE_MASK = VLQ_BASE - 1
    # binary: 100000
    VLQ_CONTINUATION_BIT = VLQ_BASE

    def __init__(self):
        self.sources = []
        self.sourcesContent = []
        self.mappings = []
        self.last_file_n = 0
        self.last_line_n = 0
        self.current_file_n = 0
        self.current_line_n = 0

    def set_current_file(self, path):
        try:
            index = self.sources.index(path)
        except ValueError:
            self.sources.append(path)
            self.sourcesContent.append([])
            index = len(self.sources) - 1
        self.current_file_n = index
        self.current_line_n = 0

    def add_line(self, line):
        self.sourcesContent[self.current_file_n].append(line)
        segment = [
            0,
            self.current_file_n - self.last_file_n,
            self.current_line_n - self.last_line_n,
            0
        ]
        self.mappings.append(''.join(map(self.encode, segment)))
        self.last_file_n = self.current_file_n
        self.last_line_n = self.current_line_n
        self.current_line_n += 1

    def as_dict(self, inline_sources=True):
        # Order matters here: it's part of the spec
        src_map = collections.OrderedDict()
        src_map['version'] = 3
        src_map['sources'] = self.sources[::]
        src_map['sourcesContent'] = self.get_sources_content() if inline_sources else []
        src_map['names'] = []
        src_map['mappings'] = ';'.join(self.mappings)
        return src_map

    def get_sources_content(self):
        return [''.join(lines) for lines in self.sourcesContent]

    def add_inline_sources(self, filename):
        with open(filename, 'r+b') as f:
            orig_map = json.load(f, object_pairs_hook=collections.OrderedDict)
            f.seek(0)
            src_map = collections.OrderedDict()
            # Copy over original values, retaining order, and injecting our new
            # `sourcesContent` after `sources`
            for key, value in orig_map.items():
                if key != 'sourcesContent':
                    src_map[key] = value
                if key == 'sources':
                    src_map['sourcesContent'] = self.get_sources_content()
            json.dump(src_map, f)

    def dump(self, f, **kwargs):
        json.dump(self.as_dict(**kwargs), f)

    def dumps(self, **kwargs):
        return json.dumps(self.as_dict(**kwargs))

    def encode(self, value):
        encoded = ''
        vlq = self.to_vlq_signed(value)
        while True:
            digit = vlq & self.VLQ_BASE_MASK
            vlq >>= self.VLQ_BASE_SHIFT
            if vlq:
                digit |= self.VLQ_CONTINUATION_BIT
            encoded += self.BASE64[digit]
            if not vlq:
                return encoded

    def to_vlq_signed(self, value):
        return ((-value) << 1) + 1 if value < 0 else (value << 1) + 0
