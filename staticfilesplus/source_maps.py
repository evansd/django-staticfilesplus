import collections
import io

try:
    import simplejson as json
except ImportError:
    import json


def copy_sources_inline(target_map_path, original_map_path):
    contents = {}
    with open(original_map_path, 'rb') as f:
        original_map = json.load(f)
    # Build mapping of original filenames to content
    for n, content in enumerate(original_map.get('sourcesContent', [])):
        contents[original_map['sources'][n]] = content
    with open(target_map_path, 'r+b') as f:
        target_map = json.load(f, object_pairs_hook=collections.OrderedDict)
        sources_content = [contents.get(name) for name in target_map['sources']]
        f.seek(0)
        output_map = collections.OrderedDict()
        # Copy over values, retaining order, and injecting our new
        # `sourcesContent` after `sources`
        for key, value in target_map.items():
            if key != 'sourcesContent':
                output_map[key] = value
            if key == 'sources':
                output_map['sourcesContent'] = sources_content
        json.dump(output_map, f)

def copy_single_source_inline(target_map_path, source_file_path):
    with io.open(source_file_path, 'rt', encoding='utf-8') as f:
        source_file = f.read()
    sources_content = [source_file]
    with open(target_map_path, 'r+b') as f:
        target_map = json.load(f, object_pairs_hook=collections.OrderedDict)
        f.seek(0)
        output_map = collections.OrderedDict()
        # Copy over values, retaining order, and injecting our new
        # `sourcesContent` after `sources`
        for key, value in target_map.items():
            if key != 'sourcesContent':
                output_map[key] = value
            if key == 'sources':
                output_map['sourcesContent'] = sources_content
        json.dump(output_map, f)


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
