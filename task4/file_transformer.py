import json


class FileTransformer:

    def __init__(self, data):
        self.data = data

    def save(self, name):
        raise NotImplementedError('Redefine save in %s.' % (self.__class__.__name__))


class JsonTransformer(FileTransformer):

    def save(self, name):
        with open(name + '.json', 'w') as json_result:
            json.dump(self.data, json_result, ensure_ascii=False, default=str, indent=4, separators=(',', ': '))


class XmlTransformer(FileTransformer):
    def json2xml(self, json_file, line_padding=""):
        result_list = list()
        json_obj_type = type(json_file)
        if json_obj_type is list:
            for sub_elem in json_file:
                result_list.append(self.json2xml(sub_elem, line_padding))
            return "\n".join(result_list)
        if json_obj_type is dict:
            for tag_name in json_file:
                sub_obj = json_file[tag_name]
                result_list.append("%s<%s>" % (line_padding, tag_name))
                result_list.append(self.json2xml(sub_obj, "\t" + line_padding))
                result_list.append("%s</%s>" % (line_padding, tag_name))
            return "\n".join(result_list)
        return "%s%s" % (line_padding, json_file)

    def save(self, name):
        with open(name + '.xml', 'w') as xml_result:
            xml_result.write(self.json2xml(self.data))


class Choicer:

    def choice(self, data, format):
        if format == 'json':
            return JsonTransformer(data)
        elif format == 'xml':
            return XmlTransformer(data)
