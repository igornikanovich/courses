import pymysql


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


class Creator(Connector):

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