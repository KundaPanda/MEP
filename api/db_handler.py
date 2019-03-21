#!/usr/bin/python3

import psycopg2
import psycopg2.pool
import time
from sh import pg_dump
import gzip
import os
from datetime import datetime


# MAXIMUM TABLE NAME LENGTH = 40 CHARACTERS


AUTH_DB_NAME = ""
AUTH_COLUMNS = ""
AUTH_TABLE_NAME = ""

# TODO: Create different classes by functionality maybe?
# TODO: refractor function arguments
# TODO: proper pool usage

DEFAULT_TABLE_NAME = "tickets"
POOL_SIZE = 100
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

    def get_pool(self, pool=None, maxconn=POOL_SIZE, user=USER, host=HOST, port=PORT, database=DB_NAME):
        """
        @in (optional) pool: ThreadedConnectionPool to handle
        create a new pool if one doesn't exist already, can also switch pool to the one provided as an argument
        """
        if not self.pool:
            if not pool:
                try:
                    connection = psycopg2.connect(
                        user=user, host=host, port=port)
                    connection.autocommit = True
                    cursor = connection.cursor()
                    sql_string = "SELECT COUNT(*) FROM pg_catalog.pg_database WHERE datname = '%s'" % database
                    cursor.execute(sql_string)
                    count = cursor.fetchone()[0]

                    if not count:
                        print("Creating database '%s'" % database)
                        sql_string = "CREATE DATABASE %s" % database
                        cursor.execute(sql_string)
                        time.sleep(0.5)
                        print("Database '%s' created!" % database)

                    connection.close()

                    connection = psycopg2.connect(
                        user=user, host=host, port=port, database=database)
                    connection.autocommit = True
                    cursor = connection.cursor()
                    table_name = AUTH_TABLE_NAME if database == AUTH_DB_NAME else DEFAULT_TABLE_NAME
                    sql_string = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '%s')" % table_name

                    cursor.execute(sql_string)
                    exists = cursor.fetchone()[0]

                    if not exists:
                        print("Creating table '%s'" % table_name)
                        if database == AUTH_DB_NAME:
                            sql_string = "CREATE TABLE %s (%s varchar(40) PRIMARY KEY, %s varchar(40))" % (
                                table_name, AUTH_COLUMNS[0], AUTH_COLUMNS[1])
                        else:
                            sql_string = "CREATE TABLE %s (%s serial PRIMARY KEY, %s varchar(40) UNIQUE, %s integer, %s TIMESTAMP)" % (
                                table_name, COLUMNS[0], COLUMNS[1], COLUMNS[2], COLUMNS[3])
                        cursor.execute(sql_string)
                        time.sleep(0.5)
                        print("Table '%s' created!" % AUTH_TABLE_NAME)

                    connection.close()

                    self.pool = psycopg2.pool.ThreadedConnectionPool(
                        maxconn=maxconn, minconn=1, user=user, host=host, port=port, database=database)
                except (psycopg2.OperationalError, Exception) as e:
                    print(e)
                    self.pool = None
                    return 1
            else:
                self.pool = pool
            print("Postgre pool built for database '%s'." % database)
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
        rollback all changes made on this cursor's connection and close the connection
        """
        if self.connection:
            self.connection.rollback()
            self.connection.close()
        if self.cursor:
            self.cursor.close()
        self.master_pool.pool.putconn(self.connection)

    def commit(self):
        """"
        commits all changes done to the database and closes the connection
        """
        if self.connection:
            self.connection.commit()
            self.connection.close()
        if self.cursor:
            self.cursor.close()
        self.master_pool.pool.putconn(self.connection)


def simple_sql_command(sql_string, cursor_wrapper=None, dispose=True):
    """
    @in str sql_string: sql_string to be executed
    @in get_cursor (optional) cursor_wrapper: get_cursor class (will create a new one if none is provided)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 0 if success else 1
    sends a single sql command to the database, returns 0/1 ONLY
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
            if dispose:
                cursor_wrapper.commit()
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            if dispose:
                cursor_wrapper.rollback()
            time.sleep(0.1)
    return 1 if i else 0


def simple_sql_select(sql_string, cursor_wrapper=None, dispose=True):
    """
    @in str sql_string: sql_string to be executed
    @in get_cursor (optional) cursor_wrapper: get_cursor class (will create a new one if none is provided)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: SELECT result if success else 1
    sends a single sql command to the database, returns SELECT result
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
            result = cursor.fetchall()
            if dispose:
                cursor_wrapper.commit()
            i = 0
            break
        except psycopg2.Error as e:
            print(e)
            if dispose:
                cursor_wrapper.rollback()
            time.sleep(0.1)
    return 1 if i else result


def select_row(colname, colvalue, table_name, cursor_wrapper=None, dispose=True):
    """
    @in str colname: column to be searched
    @in str colvalue: value to search for in the column
    @in str table_name: table to search in
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 1 if entry not found or some error occured else tuple containing the whole row with the specified code
    checks for a code in a table
    """
    colvalue = str(colvalue)
    sql_string = "SELECT * FROM %s WHERE %s = '%s'" % (
        table_name, colname, colvalue)
    # try to execute the command up to 5 times if the first try fails
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def check_and_update_code(code, table_name, cursor_wrapper=None, dispose=True):
    """"
    @in str/int  code: code to update
    @in str table_name: table to be updated
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 1 if code is not found or an error occured, else tuple containing the whole row with the specified code BEFORE THE UPDATE
    checks for a code in table (see select_row) and if a code is found, updates its data (time last requested, number of requests) and returns data before the update
    """
    global pg_pool
    while (pg_pool.check_pool() != 0):
        time.sleep(0.1)
    if not cursor_wrapper:
        cursor_wrapper = get_cursor()
    command_result = 1
    try:
        current_data = select_row(
            "code", code, table_name, cursor_wrapper, False)
        # print(current_data)
        if current_data:
            if not current_data[2]:
                used = 0
            else:
                used = current_data[2]
            sql_string = "UPDATE %s SET used=%s, time='%s' WHERE code='%s' " % (
                table_name, used + 1, datetime.now(), code)
            command_result = simple_sql_command(
                sql_string, cursor_wrapper, dispose)
        else:
            cursor_wrapper.commit()
            return 1
    except Exception as e:
        print(e)
    return 1 if command_result else current_data


def delete_entry(value, table_name, column_name, cursor_wrapper=None, dispose=True):
    # TODO COMMENT
    """
    @in array codes: array of codes to insert into the table (even for one, it must be an array)
    @in str table_name: name of the table to be added into
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 0 if success else 1
    adds 1 or more entries to a table in the database
    """
    sql_string = "DELETE FROM %s WHERE %s='%s'" % (
        table_name, column_name, value)
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
        # print(command_result)
    except Exception as e:
        print(e)
    return command_result


def add_entries(codes, table_name, cursor_wrapper=None, dispose=True, columns=COLUMNS[1]):
    """
    @in array codes: array of codes to insert into the table (even for one, it must be an array)
    @in str table_name: name of the table to be added into
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 0 if success else 1
    adds 1 or more entries to a table in the database
    """
    codes_string = ""
    for i in range(len(codes)):
        codes_string += ("('" + codes[i] + "')" + ", " * (i != len(codes) - 1))
    sql_string = "INSERT INTO %s (%s) VALUES %s" % (
        table_name, columns, codes_string)
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def get_tables(cursor_wrapper=None, dispose=True):
    """
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    returns a list of table names in the data database
    """
    sql_string = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    command_result = 1
    try:
        command_result = simple_sql_select(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def clear_table(table_name, primary_column_name=COLUMNS[0], cursor_wrapper=None, dispose=True):
    """
    @in str table_name: name of the table to be cleared
    @out: 0 if success else 1
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    deletes everything in a table and resets the id (prim. key) indexing
    """
    global pg_pool
    while (pg_pool.check_pool() != 0):
        time.sleep(0.1)
    if not cursor_wrapper:
        cursor_wrapper = get_cursor()
    cursor = cursor_wrapper.cursor
    sql_string = "DELETE FROM %s" % table_name
    sql_string2 = "SELECT setval('%s_%s_seq', 1)" % (
        table_name, primary_column_name)
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, False)
        if primary_column_name == COLUMNS[0]:
            command_result2 = simple_sql_command(
                sql_string2, cursor_wrapper, dispose)
        else:
            if dispose:
                cursor_wrapper.commit()
    except Exception as e:
        print(e)
    return 1 if (command_result) else 0


def drop_table(table_name, cursor_wrapper=None, dispose=True):
    """
    @in str table_name: name of the table to be dropped
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @out: 0 if success else 1
    drops a table
    """
    sql_string = "DROP TABLE %s" % table_name
    command_result = 1
    try:
        command_result = simple_sql_select(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def create_table(table_name, cursor_wrapper=None, dispose=True):
    """
    @in str table_name: name of the table to be created
    @out: 0 if success else 1
    creates a table
    """
    sql_string = "CREATE TABLE %s (%s serial PRIMARY KEY, %s varchar(40) UNIQUE, %s integer, %s TIMESTAMP)" % (
        table_name, COLUMNS[0], COLUMNS[1], COLUMNS[2], COLUMNS[3])
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
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
    @in bool scheduled: if the backup is ran from a scheduler (True) or on request (False)
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
