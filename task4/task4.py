import json
import argparse
import pymysql


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

    def save(self, name):
        raise NotImplementedError('Redefine save in %s.' % (self.__class__.__name__))


class JsonTransformer(Transformer):

    def save(self, name):
        with open(name + '.json', 'w') as json_result:
            json.dump(self.data, json_result, ensure_ascii=False, default=str, indent=4, separators=(',', ': '))


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

    def save(self, name):
        with open(name + '.xml', 'w') as xml_result:
            xml_result.write(self.json2xml(self.data))


class Choicer:

    def choice(self, data, format):
        if format == 'json':
            return JsonTransformer(data)
        elif format == 'xml':
            return XmlTransformer(data)


class Connector:

    def __init__(self, host: str, user: str, passw: str, db: str):
        self.host = host
        self.user = user
        self.passw = passw
        self.db = db
        self.connect = pymysql.connect(self.host, self.user, self.passw, self.db)
        self.cursor = self.connect.cursor()

    def disconnect(self):
        self.cursor.close()
        self.connect.close()


class Creater(Connector):

    def create(self, sql: str):
        try:
            self.cursor.execute(sql)
        except pymysql.Error as e:
            print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))


class Insertor(Connector):

    def insert(self, data: list, sql: str):
        values = [tuple(key.values()) for key in data]
        try:
            self.cursor.executemany(sql, values)
            self.connect.commit()
        except pymysql.Error as e:
            print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            self.connect.rollback()


class Selector(Connector):

    def select(self, sql: str):
        try:
            self.cursor.execute(sql)
            out_data = [dict(zip([key[0] for key in self.cursor.description], row)) for row in self.cursor.fetchall()]
            return out_data
        except pymysql.Error as e:
            print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))


def run(students, rooms, format, host, user, passw, database):
    students = JsonLoader(students).read()
    rooms = JsonLoader(rooms).read()
    db = Creater(host, user, passw, database)
    db.create("""CREATE TABLE IF NOT EXISTS rooms (
                         id INT NOT NULL PRIMARY KEY,
                         name VARCHAR(10)
                         ) engine=innodb default charset=utf8""")
    db.create("""CREATE TABLE IF NOT EXISTS students (
                         birthday DATE,
                         id INT NOT NULL PRIMARY KEY,
                         name VARCHAR(30),
                         room INT,
                         sex ENUM('M', 'F'),
                         FOREIGN KEY (room) REFERENCES rooms(id) 
                         ON DELETE SET NULL ON UPDATE SET NULL
                         ) engine=innodb default charset=utf8""")
    db.disconnect()
    db = Insertor(host, user, passw, database)
    db.insert(rooms, """INSERT INTO rooms (id, name) VALUES (%s,%s)""")

    db.insert(students, """INSERT INTO students (birthday, id, name, room, sex) 
                    VALUES (%s, %s, %s, %s, %s)""")
    db.disconnect()

    requests = dict(count_stud="""SELECT rooms.name, COUNT(students.id) AS num
                                    FROM rooms
                                    JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id""",
                    min_avg="""SELECT rooms.name,
                                    AVG((YEAR(CURRENT_DATE) - YEAR(students.birthday)) -
                                    (RIGHT(CURRENT_DATE, 5) < RIGHT(students.birthday, 5))) AS age
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id ORDER BY age LIMIT 5""",
                    max_diff="""SELECT rooms.name,
                                    YEAR(MAX(students.birthday)) - YEAR(MIN(students.birthday)) -
                                    (RIGHT(MAX(students.birthday), 5) < RIGHT(MIN(students.birthday), 5)) AS difference
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id ORDER BY difference DESC LIMIT 5""",
                    mf_rooms="""SELECT rooms.name
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id
                                    HAVING COUNT(DISTINCT students.sex) = 2""")

    request = Selector(host, user, passw, database)
    for name, req in requests.items():
        data = request.select(req)
        Choicer().choice(data, format).save(name)
    request.disconnect()



# Оптимизация запросов с использованием индексов на мой взгляд нецелесообразна, т.к.
# мы группируемся по колонкам, которые являются Primary Key для таблиц (room_id в rooms).
# Во время создания таблиц неявно создается индекс для колонки, которая является Primary Key.
# Использование индекса для колонок, которые используются в агрегатных функциях,
# не принесет явной оптимизации, т.к. количество записей, которые будут обрабатываться
# этими функциями, мало.
# Но это не точно)


def main():
    parser = argparse.ArgumentParser(description='Start up')
    parser.add_argument('students_file', type=str, help='Student file')
    parser.add_argument('rooms_file', type=str, help='Rooms file')
    parser.add_argument('out_format', choices=['json', 'xml'], help='choice json or xml')
    parser.add_argument('-hn', '--hostname', help='MySQL host name.', default='localhost', required=True)
    parser.add_argument('-u', '--user', help='MySQL username.', default='root', required=True)
    parser.add_argument('-p', '--password', help='Password for MySQL.', required=True)
    parser.add_argument('-d', '--database', help='MySQL database name.', default='leverxtest', required=True)
    args = parser.parse_args()
    students = args.students_file
    rooms = args.rooms_file
    format = args.out_format
    host = args.hostname
    user = args.user
    passw = args.password
    database = args.database
    run(students, rooms, format, host, user, passw, database)


if __name__ == "__main__":
    main()
