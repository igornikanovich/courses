import json

class FileLoader:

    def __init__(self, input_file):
        self.file = input_file

    def read(self):
        raise NotImplementedError('Redefine read in %s.' % (self.__class__.__name__))


class JsonLoader(FileLoader):

    def read(self):
        try:
            with open(self.file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print('Input file error')
        return data
