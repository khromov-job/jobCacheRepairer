import sqlite3


class DatabaseManager(object):
    def __init__(self, path_to_db):
        self.conn = sqlite3.connect(path_to_db)
        self.cursor = self.conn.cursor()
        self.cursor.execute("create table if not exists cache "
                            "(id integer NOT NULL PRIMARY KEY, "
                            "cache_path TEXT NOT NULL)")
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def select_all_data(self):
        self.cursor.execute("select * from cache")
        return self.cursor.fetchall()

    def select_last(self):
        self.cursor.execute("select * from cache where id = (select MAX(id) from cache)")
        return self.cursor.fetchone()

    def select(self, cache_id):
        self.cursor.execute("select * from cache where id = ?", (cache_id,))
        return self.cursor.fetchone()

    def delete_all_data(self):
        self.cursor.execute("delete from cache")
        self.conn.commit()

    def delete_last(self):
        self.cursor.execute("delete from cache where id = (select MAX(id) from cache)")
        self.conn.commit()

    def delete(self, cache_id):
        self.cursor.execute("delete from cache where id = ?", (cache_id,))
        self.conn.commit()

    def add(self, cache_path):
        self.cursor.execute("select * from cache where cache_path = (?)", (cache_path,))
        searched = self.cursor.fetchall()
        if not searched:
            self.cursor.execute("insert into cache(cache_path) values (?)", (cache_path,))
        self.conn.commit()
