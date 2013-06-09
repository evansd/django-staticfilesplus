class BaseProcessor(object):
    original_suffix = None
    processed_suffix = None

    def get_original_name(self, name):
        if name.endswith(self.processed_suffix):
            return name[:-len(self.processed_suffix)] + self.original_suffix

    def get_processed_name(self, name):
        if name.endswith(self.original_suffix):
            return name[:-len(self.original_suffix)] + self.processed_suffix

    def is_ignored_file(self, path):
        return False

    def process_file(self, input_path, output_path):
        raise NotImplementedError()
