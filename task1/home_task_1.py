import json
import argparse


class Loader:
    def __init__(self, input_file):
        self.file = input_file

    def read(self):
        raise NotImplementedError('Redefine read in %s.' % (self.__class__.__name__))


class JsonLoader(Loader):

    def read(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
            return data


class Transformer:
    def __init__(self, data):
        self.data = data

    def save(self):
        raise NotImplementedError('Redefine save in %s.' % (self.__class__.__name__))


class JsonTransformer(Transformer):
    def save(self):
        with open('result.json', 'w') as json_result:
            json.dump(self.data, json_result, indent=4)


class XmlTransformer(Transformer):
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

    def save(self):
        with open('result.xml', 'w') as xml_result:
            xml_result.write(self.json2xml(self.data))


class Choicer:
    def choice(self, data, format):
        if format == 'json':
            return JsonTransformer(data)
        elif format == 'xml':
            return XmlTransformer(data)


class Merge:
    def __init__(self, students, rooms):
        self.students = students
        self.rooms = rooms

    def merge(self):
        data = []
        [data.append({'room': i, 'students': []}) for i in range(len(self.rooms))]
        [data[i['room']]['students'].append(i) for i in self.students]
        return data


def run(students, rooms, format):
    students = JsonLoader(students).read()
    rooms = JsonLoader(rooms).read()
    data = Merge(students, rooms).merge()
    choice = Choicer().choice(data, format)
    choice.save()


def main():
    parser = argparse.ArgumentParser(description='Merge rooms and students')
    parser.add_argument('students_file', type=str, help='Student file')
    parser.add_argument('rooms_file', type=str, help='Rooms file')
    parser.add_argument('out_format', choices=['json', 'xml'], help='choice json or xml')
    args = parser.parse_args()
    students = args.students_file
    rooms = args.rooms_file
    format = args.out_format
    run(students, rooms, format)


if __name__ == "__main__":
    main()
