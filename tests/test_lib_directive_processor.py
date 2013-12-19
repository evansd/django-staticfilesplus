from __future__ import absolute_import, unicode_literals

import itertools
from unittest import TestCase
from textwrap import dedent

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from staticfilesplus.lib.directive_processor import (DirectiveProcessor,
        DirectiveError)

def clean(s):
    return dedent(s.lstrip('\n')).rstrip()

def get_lines(text):
    for line in clean(text).splitlines(True):
        if line[-1] != '\n':
            line += '\n'
        yield line

def get_file_lines(self, path):
    return get_lines(FILESYSTEM[path])


class DirectiveProcessorParsingTest(TestCase):

    def test_extract_header(self):
        for num_header_lines, s in [
                (1, '// simple'),
                (1, '   # simple'),
                (1, ' /* in * line */'),
                (1, ' /* inline */ # stuff after'),
                (3, ' /* \n multiline \n */'),
                (3, ' /* \n split */  /* inline */  /* \n up */'),
                (1, ' # mixed */'),
                (0, ' /* inline */ stuff after'),
                (0, 'close without open */  /* */'),
                (0, '/* comment */ notcomment /* more */'),
                (0, 'notcomment /* more */'),
                (1, '/* mutli\nline */ after'),
                ]:
            matched_num_header_lines = 0
            for line, is_header in DirectiveProcessor.extract_header(get_lines(s)):
                if is_header:
                    matched_num_header_lines += 1
            self.assertEqual(num_header_lines, matched_num_header_lines, msg=s)

    def assertDirectives(self, contents, target):
        lines = get_lines(contents)
        directives = [directive for line, directive in
                DirectiveProcessor.extract_directives(lines)
                if directive]
        self.assertEqual(directives, target)

    def test_parse_single_directive(self):
        self.assertDirectives("""
            //= require hello
            """, [
            ('require', 'hello'),
        ])

    def test_parse_multiple_directives(self):
        self.assertDirectives("""
            /*
            * =require hello
            *
            * =require "hello there"
            */
            """, [
            ('require', 'hello'),
            ('require', 'hello there')
        ])

    def test_directives_after_non_comment_ignored(self):
        self.assertDirectives("""
            window.blahblah();
            //= require hello
            """, [])

    def test_errors_raised(self):
        with self.assertRaises(DirectiveError):
            list(DirectiveProcessor.extract_directives(
                    get_lines('//= require "no closing')))


FILESYSTEM = {
    '/lib1/test.js': """
        //= require somelib
        //= require ./localfile
        hello
        """,
    '/lib1/localfile.js': """
        //= require ./sub/morelocal.js
        //= require otherlib.js
        some content
        """,
    '/lib1/sub/morelocal.js': """
        more local
        """,
    '/lib2/somelib.js': """
        //= stub otherlib
        nothing much here
        """,
    '/lib2/otherlib.js': """
        should not be included
        """,
}

class io_open(object):

    def __init__(self, path, mode, encoding):
        assert mode == 'rt'
        assert encoding == 'utf-8'
        self.path = path

    def __enter__(self):
        return (line for line in clean(FILESYSTEM[self.path]).splitlines(True))

    def __exit__(self, *args):
        pass

@patch('staticfilesplus.lib.directive_processor.io.open', new=io_open)
@patch('staticfilesplus.lib.directive_processor.os.path.exists', new=FILESYSTEM.__contains__)
class DirectiveProcessorTest(TestCase):

    def test_processing(self):
        processor = DirectiveProcessor('/lib1/test.js', load_paths=['/lib1', '/lib2'])
        lines = itertools.chain(*[f[1] for f in processor.output])
        self.assertEqual(list(lines), list(get_lines("""
            //= stub otherlib
            nothing much here
            more local
            //= require ./sub/morelocal.js
            //= require otherlib.js
            some content
            //= require somelib
            //= require ./localfile
            hello
            """)))
