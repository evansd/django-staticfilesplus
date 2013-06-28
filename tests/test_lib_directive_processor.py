from __future__ import absolute_import, unicode_literals

from unittest import TestCase
from textwrap import dedent

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from staticfilesplus.lib.directive_processor import DirectiveProcessor

def clean(s):
    return dedent(s.lstrip('\n')).rstrip()

class DirectiveProcessorTest(TestCase):

    def assertDirectives(self, contents, directives):
        contents = clean(contents)
        parsed = DirectiveProcessor().extract_directives(contents)
        self.assertEqual(parsed[0], directives)

    def test_parse_single_directive(self):
        self.assertDirectives("""
            //= require hello
            """, [
            (1, 'require', 'hello'),
        ])

    def test_parse_multiple_directives(self):
        self.assertDirectives("""
            /*
            * =require hello
            *
            * =require "hello there"
            */
            """, [
            (2, 'require', 'hello'),
            (4, 'require', 'hello there')
        ])

    def test_directives_after_non_comment_ignored(self):
        self.assertDirectives("""
            window.blahblah();
            //= require hello
            """, [
        ])

    def test_errors_raised(self):
        with self.assertRaises(DirectiveProcessor.DirectiveError):
            DirectiveProcessor().extract_directives('//= require "no closing')

    @patch('staticfilesplus.lib.directive_processor.os.path.exists')
    def test_file_finding(self, mock_os_exists):
        # Mock os.path.exists so it returns True just for the files
        # we list here
        filesystem = set((
            '/home/lib1/testfile.js',
            '/home/lib1/testfile2.js',
        ))
        mock_os_exists.side_effect = filesystem.__contains__
        processor = DirectiveProcessor(load_paths=['/home/lib1', '/home/lib2'])
        find_path = processor.find_path
        self.assertEqual(find_path('testfile.js', ''), '/home/lib1/testfile.js')
        self.assertEqual(find_path('./testfile2', '/home/lib1/testfile.js'),
                '/home/lib1/testfile2.js')

    @patch('staticfilesplus.lib.directive_processor.DirectiveProcessor.get_file_contents')
    @patch('staticfilesplus.lib.directive_processor.os.path.exists')
    def test_processing(self, mock_os_exists, mock_get_file_contents):
        # Mock out the filesystem
        filesystem = {
            '/lib1/test.js': clean("""
                //= require somelib
                //= require ./localfile
                """),
            '/lib1/localfile.js': clean("""
                //= require ./sub/morelocal.js
                //= require otherlib.js
                some content
                """),
            '/lib1/sub/morelocal.js': clean("""
                more local
                """),
            '/lib2/somelib.js': clean("""
                //= stub otherlib
                nothing much here
                """),
            '/lib2/otherlib.js': clean("""
                should not be included
                """),
        }
        mock_get_file_contents.side_effect = lambda n: filesystem[n]
        mock_os_exists.side_effect = filesystem.__contains__
        processor = DirectiveProcessor(load_paths=['/lib1', '/lib2'])
        load = processor.load
        self.assertEqual(load('test.js'), clean("""
            nothing much here
            more local
            some content
            """)+"\n")



