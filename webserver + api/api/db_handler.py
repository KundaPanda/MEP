#!/usr/bin/python3

import psycopg2
import psycopg2.pool
import time
from sh import pg_dump
import gzip
import os
from datetime import datetime

# TODO: Create different classes by functionality maybe?

POOL_SIZE = 200
COLUMNS = ("id", "code", "used", "time")
USER = "postgres"
DB_NAME = "tickets"
PORT = "5432"
HOST = "localhost"
BACKUP_NAMES = ["backup_latest.gz"]
for i in range(1, 10):
    i = str(i)
    BACKUP_NAMES.append("backup" + "0" * (2 - len(i)) + i + ".gz")
BACKUP_PATH = os.path.abspath("backups")

postgre_pool = None


class get_cursor:
    global postgre_pool

    def __init__(self):
        if postgre_pool:
            self.connection = postgre_pool.getconn()
            if self.connection:
                self.cursor = self.connection.cursor()
            else:
                self.cursor = None
                print("Invalid connection supplied, aborting.")
        else:
            print("No valid pool, aborting.")

    def rollback(self):
        if self.connection:
            self.connection.rollback()

    def dispose(self):
        if self.connection and self.cursor:
            self.cursor.close()
            self.connection.close()
            print("PUTCONN")
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
                maxconn=POOL_SIZE, minconn=1, user=USER, host=HOST, port=PORT, database=DB_NAME)
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


def free_pool():
    global postgre_pool
    if postgre_pool:
        postgre_pool.closeall()
    print("Postgre pool reset.")


def check_pool():
    if not postgre_pool:
        print("No pool, creating a new one.")
        while not postgre_pool:
            get_pool()
            time.sleep(0.1)
    return 1


def simple_sql_command(sql_string, cursor_wrapper=None):
    if cursor_wrapper:
        cursor = cursor_wrapper.cursor
    else:
        cursor_wrapper = get_cursor()
        cursor = cursor_wrapper.cursor
    for i in range(5):
        try:
            cursor.execute(sql_string)
            cursor_wrapper.commit()
            cursor_wrapper.dispose()
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            cursor_wrapper.rollback()
            cursor_wrapper.dispose()
            time.sleep(0.1)
    return 1 if i else 0


def select_code(code, table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    code = str(code)
    sql_string = "SELECT * FROM %s WHERE code = '%s'" % (table_name, code)
    for i in range(5):
        try:
            cursor.execute(sql_string)
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            time.sleep(0.1)
    if i:
        return None
    result = cursor.fetchone()
    cursor_wrapper.dispose()
    return result


def check_and_update_code(code, table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    current_data = select_code(code, table_name)
    # print(current_data)
    if current_data:
        if not current_data[2]:
            used = 0
        else:
            used = current_data[2]
        sql_string = "UPDATE %s SET used=%s, time='%s' WHERE code='%s' " % (
            table_name, used + 1, datetime.now(), code)
        command_result = simple_sql_command(sql_string)
    else:
        return 1
    return current_data if not command_result else 1


def add_entries(codes, table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    codes_string = ""
    for i in range(len(codes)):
        codes_string += (codes[i] + ", " * (i != len(codes) - 1))
    # format_string = "".join("%s, " for _ in range(len(codes)))
    sql_string = "INSERT INTO %s (code) VALUES %s" % (table_name, codes_string)
    # print(sql_string)
    command_result = simple_sql_command(sql_string)
    return 1 if command_result else 0


def clear_table(table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    sql_string = "DELETE FROM %s" % table_name
    for i in range(5):
        try:
            cursor.execute(sql_string)
            sql_string = "SELECT setval('%s_id_seq', 1)" % table_name
            cursor.execute(sql_string)
            cursor_wrapper.commit()
            cursor_wrapper.dispose()
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            cursor_wrapper.rollback()
            cursor_wrapper.dispose()
            time.sleep(0.1)
    return 1 if i else 0


def drop_table(table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    sql_string = "DROP TABLE %s" % table_name
    command_result = simple_sql_command(sql_string)
    return command_result


def create_table(table_name):
    while (check_pool() != 1):
        time.sleep(0.1)
    sql_string = (
        "CREATE TABLE %s (id serial PRIMARY KEY, code varchar(40) UNIQUE, used integer, time TIMESTAMP)" % table_name)
    print(sql_string)
    command_result = simple_sql_command(sql_string)
    return command_result


def rename_backups(index):
    file_path = os.path.join(BACKUP_PATH, BACKUP_NAMES[index])
    if os.path.isfile(file_path):
        if index == 9:
            os.remove(file_path)
        else:
            rename_backups(index + 1)
            os.rename(file_path,
                      os.path.join(BACKUP_PATH, BACKUP_NAMES[index + 1]))


def create_backup(scheduled=True):
    if scheduled:
        print("Starting scheduled database backup.")
    else:
        print("Starting requested database backup.")
    rename_backups(0)
    try:
        latest_file_path = os.path.join(BACKUP_PATH, "backup_latest.gz")
        with open(latest_file_path, "wb") as f:
            pg_dump('-h', HOST, '-U', USER, DB_NAME, _out=f)
        print("Backup successful! @ %s" % time.strftime(
            "%a, %d %b %Y %H:%M:%S", time.gmtime()))
        return 0
    except Exception as e:
        print(e)
        return 1
