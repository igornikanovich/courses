import argparse

from file_loader import JsonLoader
from file_transformer import Choicer
from db_operations import Creator, Insertor, Selector


def run(students, rooms, format, config):
    students = JsonLoader(students).read()
    rooms = JsonLoader(rooms).read()
    db = Creator(config)
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
    db.create("""CREATE INDEX room_birthday_index ON students(room, birthday)""")
    db.create("""CREATE INDEX room_sex_index ON students(room, sex)""")
    db.disconnect()
    db = Insertor(config)
    db.insert(rooms, """INSERT INTO rooms (id, name) VALUES (%s,%s)""")

    db.insert(students, """INSERT INTO students (birthday, id, name, room, sex) 
                    VALUES (%s, %s, %s, %s, %s)""")
    db.disconnect()

    requests = dict(count_stud="""SELECT rooms.name, COUNT(students.id) AS num
                                    FROM rooms
                                    LEFT JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id""",
                    min_avg="""SELECT rooms.name
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id
                                    ORDER BY AVG(students.birthday) DESC
                                    LIMIT 5""",
                    max_diff="""SELECT rooms.name,
                                    (DATEDIFF(MAX(students.birthday), MIN(students.birthday))/365.25) AS difference
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id ORDER BY difference DESC LIMIT 5""",
                    diff_sex_rooms="""SELECT rooms.name
                                    FROM rooms JOIN students ON rooms.id = students.room
                                    GROUP BY rooms.id
                                    HAVING COUNT(DISTINCT students.sex) > 1""")

    request = Selector(config)
    for name, req in requests.items():
        data = request.select(req)
        Choicer().choice(data, format).save(name)
    request.disconnect()



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
    config = {'host': args.hostname, 'user': args.user, 'password': args.password, 'database': args.database}
    run(students, rooms, format, config)


if __name__ == "__main__":
    main()
