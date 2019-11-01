import pymysql


class Connector:

    def __init__(self, config):
        self.config = config
        self.connect = pymysql.connect(**self.config)
        self.cursor = self.connect.cursor()

    def disconnect(self):
        self.cursor.close()
        self.connect.close()


class Creator(Connector):

    def create(self, sql: str):
        with self.connect:
            self.cursor.execute(sql)



class Insertor(Connector):

    def insert(self, data: list, sql: str):
        values = [tuple(key.values()) for key in data]
        with self.connect:
            self.cursor.executemany(sql, values)
            self.connect.commit()


class Selector(Connector):

    def select(self, sql: str):
        with self.connect:
            self.cursor.execute(sql)
            out_data = [dict(zip([key[0] for key in self.cursor.description], row)) for row in self.cursor.fetchall()]
            return out_data
