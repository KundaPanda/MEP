#!C:/Users/vojdo/AppData/Local/Programs/Python/Python37/python.exe

import psycopg2
import psycopg2.pool
import time

POOL_SIZE = 200
COLUMNS = ("id", "code", "used", "time")

postgre_pool = None


class get_cursor:
    def __init__(self):
        self.connection = postgre_pool.getconn()
        if self.connection:
            self.cursor = self.connection.cursor()
        else:
            self.cursor = None
            print("Invalid connection supplied, aborting.")

    def rollback(self):
        if self.connection:
            self.connection.rollback()

    def dispose(self):
        if self.connection and self.cursor:
            self.cursor.close()
            self.connection.close()
            postgre_pool.putconn(self.connection)
            self.connection = None
            self.cursor = None

    def commit(self):
        if self.connection:
            self.connection.commit()


def get_pool(pool=None):
    global postgre_pool
    if pool:
        postgre_pool = pool
    if not postgre_pool:
        try:
            postgre_pool = psycopg2.pool.ThreadedConnectionPool(
                maxconn=POOL_SIZE, minconn=4, user="postgres", password="kundapanda", host="localhost", port="5432", database="tickets")
        except (psycopg2.OperationalError, Exception) as e:
            print(e)
            postgre_pool = None
        print("Postgre pool built.")
    return postgre_pool


def close_pool():
    global postgre_pool
    if postgre_pool:
        postgre_pool.closeall()
    print("Postgre pool closed.")
    return 1


def check_pool():
    if not postgre_pool:
        print("No pool, creating a new one.")
        while not postgre_pool:
            get_pool()
            time.sleep(0.1)
    return 1


def select_code(code, table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    code = str(code)
    sql_string = "SELECT * FROM %s WHERE code = '%s'" % (table_name, code)
    try:
        cursor.execute(sql_string)
    except psycopg2.Error as e:
        print(e)
        return None
    result = cursor.fetchone()
    cursor_wrapper.dispose()
    return result


def add_entry(code, table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    sql_string = "INSERT INTO %s(code) VALUES('%s')" % (table_name, code)
    try:
        cursor.execute(sql_string)
        cursor_wrapper.commit()
        cursor_wrapper.dispose()
        return 0
    except psycopg2.Error as e:
        print(e, "Rolling back changes.")
        cursor_wrapper.rollback()
        cursor_wrapper.dispose()
        return 1


def dump_database():
    while (check_pool() != 1):
        check_pool()
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    sql_string = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"""
    try:
        cursor.execute(sql_string)
    except psycopg2.Error as e:
        print(e)
        return None
    tables = cursor.fetchall()
    result = {}
    for table in tables:
        sql_string = "SELECT * FROM %s" % (table)
        cursor.execute(sql_string)
        result[table[0]] = cursor.fetchall()
    cursor_wrapper.dispose()
    return result


def clear_table(name):
    while (check_pool() != 1):
        check_pool()
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    sql_string = "DELETE FROM %s" % name
    try:
        cursor.execute(sql_string)
        cursor.execute("SELECT setval('tickets_id_seq', 1)")
        cursor_wrapper.commit()
        cursor_wrapper.dispose()
    except psycopg2.Error as e:
        print(e)
        cursor_wrapper.rollback()
        cursor_wrapper.dispose()
        return 1
    print("CLEARED")
    return 0
