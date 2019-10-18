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

    def save(self):
        raise NotImplementedError('Redefine save in %s.' % (self.__class__.__name__))


class JsonTransformer(Transformer):

    def save(self):
        with open('result.json', 'w') as json_result:
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

    def save(self):
        with open('result.xml', 'w') as xml_result:
            xml_result.write(self.json2xml(self.data))


class Choicer:

    def choice(self, data, format):
        if format == 'json':
            return JsonTransformer(data)
        elif format == 'xml':
            return XmlTransformer(data)


class CreaterSQL:

    def __init__(self, host: str, user: str, passw: str, db: str, sql: str):
        self.host = host
        self.user = user
        self.passw = passw
        self.db = db
        self.sql = sql

    def create(self):
        raise NotImplementedError('Redefine create in %s.' % (self.__class__.__name__))


class CreateDB(CreaterSQL):

    def create(self):
        db = pymysql.connect(self.host, self.user, self.passw)
        cursor = db.cursor()
        try:
            cursor.execute("DROP DATABASE IF EXISTS {}".format(self.db))
            cursor.execute(self.sql)
        except pymysql.Error as e:
            print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
        finally:
            db.close()

class CreateTable(CreaterSQL):

    def create(self):
        db = pymysql.connect(self.host, self.user, self.passw, self.db)
        cursor = db.cursor()
        cursor.execute(self.sql)
        db.close()

class UploaderJSONtoSQL:

    def __init__(self, host: str, user: str, passw: str, db: str, data: list, sql: str):
        self.host = host
        self.user = user
        self.passw = passw
        self.db = db
        self.data = data
        self.sql = sql

    def upload(self):
        values = [tuple(key.values()) for key in self.data]
        db = pymysql.connect(self.host, self.user, self.passw, self.db)
        cursor = db.cursor()
        try:
            cursor.executemany(self.sql, values)
            db.commit()
        except Exception as e:
            print('Error loading data \n', e)
            db.rollback()
        finally:
            db.close()


class RequestorSQL:

    def __init__(self, host: str, user: str, passw: str, db: str, sql):
        self.host = host
        self.user = user
        self.passw = passw
        self.db = db
        self.sql = sql

    def request(self):
        db = pymysql.connect(self.host, self.user, self.passw, self.db)
        cursor = db.cursor()
        try:
            cursor.execute(self.sql)
            out_data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
            return out_data
        except Exception as e:
            print('Error loading data \n', e)
        finally:
            db.close()




def run(students, rooms, format, host, user, passw, database, request):
    students = JsonLoader(students).read()
    rooms = JsonLoader(rooms).read()
    db = CreateDB(host, user, passw, database, "CREATE DATABASE {}".format(database))
    db.create()

    tableRooms = CreateTable(host, user, passw, database, """CREATE TABLE rooms (
                                                                     room_id INT NOT NULL PRIMARY KEY,
                                                                     room_name VARCHAR(10)
                                                                     ) engine=innodb default charset=utf8""")
    tableRooms.create()

    tableStudents = CreateTable(host, user, passw, database, """CREATE TABLE students (
                                                                     birthday DATE,
                                                                     student_id INT NOT NULL PRIMARY KEY,
                                                                     student_name VARCHAR(30),
                                                                     room_id INT,
                                                                     sex ENUM('M', 'F'),
                                                                     FOREIGN KEY (room_id) REFERENCES rooms(room_id) 
                                                                     ON DELETE SET NULL ON UPDATE SET NULL
                                                                     )""")
    tableStudents.create()

    uploadRoomsToSQL = UploaderJSONtoSQL(host, user, passw, database, rooms, """INSERT INTO rooms (room_id, room_name) VALUES (%s,%s)""")
    uploadRoomsToSQL.upload()

    uploadStudentsToSQL = UploaderJSONtoSQL(host, user, passw, database, students,
                                            """INSERT INTO students (birthday, student_id, student_name, room_id, sex) 
                                               VALUES (%s, %s, %s, %s, %s)""")
    uploadStudentsToSQL.upload()
    if request == '1':
        request1 = RequestorSQL(host, user, passw, database, """SELECT rooms.room_name, COUNT(students.student_id) AS countStudents
                                                                FROM rooms, students
                                                                WHERE rooms.room_id=students.room_id
                                                                GROUP BY rooms.room_id""")
        req1 = request1.request()
        choice = Choicer().choice(req1, format)
        choice.save()
    elif request == '2':
        request2 = RequestorSQL(host, user, passw, database, """SELECT rooms.room_name,
                    AVG((YEAR(CURRENT_DATE)-YEAR(students.birthday))-(RIGHT(CURRENT_DATE,5)<RIGHT(students.birthday,5))) AS age
                    FROM rooms, students
                    WHERE rooms.room_id=students.room_id
                    GROUP BY room_name ORDER BY age LIMIT 5""")
        req2 = request2.request()
        choice = Choicer().choice(req2, format)
        choice.save()
    elif request == '3':
        request3 = RequestorSQL(host, user, passw, database, """SELECT rooms.room_id,
        YEAR(MAX(students.birthday))-YEAR(MIN(students.birthday))-(RIGHT(MAX(students.birthday),5)<RIGHT(MIN(students.birthday),5)) AS difference
        FROM rooms, students
        WHERE rooms.room_id=students.room_id
        GROUP BY room_id ORDER BY difference DESC LIMIT 5""")
        req3 = request3.request()
        choice = Choicer().choice(req3, format)
        choice.save()
    elif request == '4':
        request4 = RequestorSQL(host, user, passw, database, """SELECT rooms.room_name FROM students, rooms
                                                                WHERE students.room_id = rooms.room_id
                                                                GROUP BY rooms.room_id
                                                                HAVING COUNT(DISTINCT students.sex) = 2""")
        req4 = request4.request()
        choice = Choicer().choice(req4, format)
        choice.save()



def main():
    parser = argparse.ArgumentParser(description='Start up')
    parser.add_argument('students_file', type=str, help='Student file')
    parser.add_argument('rooms_file', type=str, help='Rooms file')
    parser.add_argument('out_format', choices=['json', 'xml'], help='choice json or xml')
    parser.add_argument('-hn', '--hostname', help='MySQL host name.', default='localhost', required=True)
    parser.add_argument('-u', '--user', help='MySQL username.', default='root', required=True)
    parser.add_argument('-p', '--password', help='Password for MySQL.', required=True)
    parser.add_argument('-d', '--database', help='MySQL database name.', default='leverxtest', required=True)
    parser.add_argument('-r', '--request', choices=['1', '2', '3', '4'], help='Request to database.', required=True)
    args = parser.parse_args()
    students = args.students_file
    rooms = args.rooms_file
    format = args.out_format
    host = args.hostname
    user = args.user
    passw = args.password
    database = args.database
    request = args.request
    run(students, rooms, format, host, user, passw, database, request)


if __name__ == "__main__":
    main()
