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


class postgre_pool:
    """
    stores and manages a pool
    """

    def __init__(self, pool=None):
        self.pool = pool

    def get_pool(self, pool=None):
        """
        @in (optional) pool: ThreadedConnectionPool to handle
        create a new pool if one doesn't exist already, can also switch pool to the one provided as an argument
        """
        if not self.pool:
            if not pool:
                try:
                    self.pool = psycopg2.pool.ThreadedConnectionPool(
                        maxconn=POOL_SIZE, minconn=1, user=USER, host=HOST, port=PORT, database=DB_NAME)
                except (psycopg2.OperationalError, Exception) as e:
                    print(e)
                    self.pool = None
                    return 1
            else:
                self.pool = pool
            print("Postgre pool built.")
        return self.pool

    def close_pool(self, pool=None):
        """
        @in (optional) pool: pool to be closed
        closes either its own or the provided pool
        """
        try:
            if pool:
                pool.closeall()
            elif self.pool:
                self.pool.closeall()
            else:
                print("No pool to close.")
                return 1
            print("Postgre pool closed.")
            return 0
        except Exception as e:
            print("Invalid pool supplied.")
            return 1

    def check_pool(self, pool=None):
        """
        @in (optional) pool: pool to be checked
        checks if either its own or the provided pool is valid and if not, creates a new one
        also stores provided pool as its own pool
        """
        if not pool:
            if not self.pool:
                print("No pool, creating a new one.")
                while not self.pool:
                    try:
                        self.get_pool()
                        time.sleep(0.1)
                    except Exception:
                        print("Unable to create a pool.")
                        return 1
            else:
                return 0
        elif pool:
            self.pool = pool
            try:
                conn = self.pool.getconn()
                self.pool.putconn(conn)
            except Exception as e:
                print(e)
                return 1
        return 0


pg_pool = postgre_pool()


class get_cursor:
    """
    creates and manages a cursor and its corresponding connection
    """
    global pg_pool

    def __init__(self, master_pool=pg_pool):
        """
        creates a cursor and a connection if a pool exists
        """
        if master_pool:
            self.master_pool = master_pool
            self.connection = self.master_pool.pool.getconn()
            if self.connection:
                self.cursor = self.connection.cursor()
            else:
                self.cursor = None
                print("Invalid connection supplied, aborting.")
        else:
            print("No valid pool, aborting.")

    def rollback(self):
        """
        rollback all changes made on this cursor's connection
        """
        if self.connection:
            self.connection.rollback()

    def dispose(self):
        """
        safely closes the cursor and its connection to the pool
        """
        if self.connection and self.cursor:
            self.cursor.close()
            self.connection.close()
            self.master_pool.pool.putconn(self.connection)
            self.connection = None
            self.cursor = None

    def commit(self):
        """"
        commits all changes done to the database
        """
        if self.connection:
            self.connection.commit()


def simple_sql_command(sql_string, cursor_wrapper=None):
    """
    @in str sql_string: sql_string to be executed
    @in get_cursor (optional) cursor_wrapper: get_cursor class (will create a new one if none is provided)
    @out: 0 if success else 1
    sends a single sql command to the database
    """
    global pg_pool
    if cursor_wrapper:
        cursor = cursor_wrapper.cursor
    else:
        while (pg_pool.check_pool() != 0):
            time.sleep(0.1)
        cursor_wrapper = get_cursor()
        cursor = cursor_wrapper.cursor
    # try to execute the command up to 5 times if the first try fails
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
    """
    @in str/int code: code to search for in the database
    @in str table_name: table to search in
    @out: 1 if entry not found or some error occured else tuple containing the whole row with the specified code
    checks for a code in a table
    """
    global pg_pool
    while (pg_pool.check_pool() != 0):
        time.sleep(0.1)
    cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    code = str(code)
    sql_string = "SELECT * FROM %s WHERE code = '%s'" % (table_name, code)
    # try to execute the command up to 5 times if the first try fails
    for i in range(5):
        try:
            cursor.execute(sql_string)
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            time.sleep(0.1)
    if i:
        return 1
    result = cursor.fetchone()
    cursor_wrapper.dispose()
    if not result:
        result = 1
    return result


def check_and_update_code(code, table_name):
    """"
    @in str/int  code: code to update
    @in str table_name: table to be updated
    @out: 1 if code is not found or an error occured, else tuple containing the whole row with the specified code BEFORE THE UPDATE
    checks for a code in table (see select_code) and if a code is found, updates its data (time last requested, number of requests) and returns data before the update
    """
    global pg_pool
    while (pg_pool.check_pool() != 0):
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
    """
    @in array codes: array of codes to insert into the table (even for one, it must be an array)
    @in str table_name: name of the table to be added into
    @out: 0 if success else 1
    adds 1 or more entries to a table in the database
    """
    codes_string = ""
    for i in range(len(codes)):
        codes_string += (codes[i] + ", " * (i != len(codes) - 1))
    sql_string = "INSERT INTO %s (code) VALUES %s" % (table_name, codes_string)
    command_result = simple_sql_command(sql_string)
    return 1 if command_result else 0


def clear_table(table_name):
    """
    @in str table_name: name of the table to be cleared
    @out: 0 if success else 1
    deletes everything in a table and resets the id (prim. key) indexing
    """
    global pg_pool
    while (pg_pool.check_pool() != 0):
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
    """
    @in str table_name: name of the table to be dropped
    @out: 0 if success else 1
    drops a table
    """
    sql_string = "DROP TABLE %s" % table_name
    command_result = simple_sql_command(sql_string)
    return command_result


def create_table(table_name):
    """
    @in str table_name: name of the table to be created
    @out: 0 if success else 1
    creates a table
    """
    sql_string = (
        "CREATE TABLE %s (id serial PRIMARY KEY, code varchar(40) UNIQUE, used integer, time TIMESTAMP)" % table_name)
    print(sql_string)
    command_result = simple_sql_command(sql_string)
    return command_result


def rename_backups(index=0):
    """
    automatically renames backus to the pre-defined structure
    shifts all backup indexes by one, deletes the oldest
    -> backup_latest will be available for creation
    """
    file_path = os.path.join(BACKUP_PATH, BACKUP_NAMES[index])
    if os.path.isfile(file_path):
        if index == 9:
            os.remove(file_path)
        else:
            rename_backups(index + 1)
            os.rename(file_path,
                      os.path.join(BACKUP_PATH, BACKUP_NAMES[index + 1]))


def create_backup(scheduled=True):
    """
    creates a predefined backup structure
    @in bool scheduled: if the backup is ran from a scheduler (True) or on demand (False)
    """
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
