import sqlite3


class DB:
    def __init__(self, database):
        self.db_name = database
        self.start()

    
    def conn(self):
        self.db = sqlite3.connect(self.db_name)

    def cur(self):
        self.curs = self.db.cursor()

    def save_db(self):
        self.db.commit()

    def start(self):
        self.conn()
        self.cur()

    def reset(self):
        self.db.close()
        self.start()

    def row_fac(self):
        self.db.row_factory = sqlite3.Row
        self.cur()


    def query(self, sql_query):
        self.curs.execute(sql_query)
        self.save_db()

    def select(self, select, table, where="1", order_by="id", sort_by="DESC"):
        return self.curs.execute(f"SELECT {select} FROM {table} WHERE {where} ORDER BY {order_by} {sort_by};")

    def insert(self, table, values, column=""):
        val_len = ', '.join(['?' for i in values])
        query_to = f"INSERT INTO {table}{column} VALUES({val_len});"

        last_id = self.curs.execute(query_to, values).lastrowid
        self.save_db()
        return last_id

    def insertmany(self, table, values, column=""):
        val_len = ', '.join(['?' for i in values[0]])
        query_to = f"INSERT INTO {table}{column} VALUES({val_len});"

        self.curs.executemany(query_to, values)
        self.save_db()

    def delete(self, table, where):
        delete = self.curs.execute(f"DELETE FROM {table} WHERE {where};")
        self.save_db()
        return delete


    def get_dict(self, col, table, where="1", order_by="id", sort_by="DESC"):
        self.row_fac()
        my_channel = self.select(col, table, where, order_by, sort_by).fetchall()
        self.reset()
        return self.dictionary(my_channel)    

    def dictionary(self, select):
        dicti = {}
        for id_row, name, url in select:
            if name in dicti:
                name = f"{name}_{id_row}"
            dicti[name] = id_row, url
        return dicti

def main():
    def convert_to_binary_data(filename):
        # Преобразование данных в двоичный формат
        with open(filename, 'rb') as file:
            blob_data = file.read()
        return blob_data

    db = DB("Channel.db")

    db.delete(table="Videos", where="name = 'Используй только свободные программы!'")

    # db.row_fac()
    # input(db.select('id', 'My_image').fetchone()[0])
    # input(dir(db.select('id, name, url', 'Channel')))

if __name__ == "__main__":
    main()
