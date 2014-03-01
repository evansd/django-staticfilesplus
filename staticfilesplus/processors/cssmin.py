from .base import BaseProcessor, ProcessorNotUsed


class CSSMinProcessor(BaseProcessor):

    input_extension = '.css'
    output_extension = '.css'
    supports_source_maps = False

    def __init__(self, *args, **kwargs):
        super(CSSMinProcessor, self).__init__(*args, **kwargs)
        if not self.minify_enabled:
            raise ProcessorNotUsed()
        self.cssmin_bin = getattr(self.settings,
                'STATICFILESPLUS_CSSMIN_BIN', 'cssmin')

    def process(self, input_name, input_path, outputs):
        output_path = outputs[0][1]
        if not self.any_files_modified_since(output_path, [input_path]):
            return outputs
        with self.create(output_path) as f:
            self.call_command([self.cssmin_bin, input_path], stdout=f)
        return outputs
