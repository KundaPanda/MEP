#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
BACKUP_NAMES = ["backup_latest_%s.gz" % DB_NAME]
for i in range(1, 10):
    i = str(i)
    BACKUP_NAMES.append("backup" + "0" * (2 - len(i)) + i + "_%s.gz" % DB_NAME)
BACKUP_PATH = os.path.abspath("backups")


class postgre_pool:
    """
    stores and manages a pool
    """

    def __init__(self, pool=None):
        self.pool = pool

    def get_pool(self, pool=None, maxconn=POOL_SIZE, user=USER, host=HOST, port=PORT, database=DB_NAME):
        """creates a pool based on parameters and sets it as self.pool

        Keyword Arguments:
            pool {[string]} -- [postgre_pool.pool object] (default: {None})
            maxconn {[string]} -- [maximum number of connections] (default: {POOL_SIZE})
            user {[string]} -- [username for db login] (default: {USER})
            host {[string]} -- [hostname for db login] (default: {HOST})
            port {[string]} -- [port for db login] (default: {PORT})
            database {[string]} -- [db name for db login] (default: {DB_NAME})

        Returns:
            [postgre_pool.pool] -- [pool object]
        """

        if not self.pool:
            if not pool:
                try:
                    # if there is no pool, check for database validity and create a new one
                    create_database_if_not_exists(database, user, host, port)
                    create_default_table_if_not_exists(
                        database, user, host, port)
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
        """closes either its own or the provided pool

        Keyword Arguments:
            pool {[postgre_pool.pool]} -- [pool to be closed] (default: {self.pool})

        Returns:
            [boolean] -- [False if closed, True if it doesn't exist or is invalid]
        """

        # if pool is provided, close all its connections
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
        except Exception:
            print("Invalid pool supplied.")
            return 1

    def check_pool(self, pool=None):
        """checks if either its own or the provided pool is valid

        Keyword Arguments:
            pool {[postgre_pool.pool]} -- [pool to be checked] (default: {self.pool})

        Returns:
            [boolean] -- [False if exists, True if it doesn't or is invalid]
        """

        if not pool:
            if not self.pool:
                return 1
            else:
                try:
                    test_connection = self.pool.getconn()
                    self.pool.putconn(test_connection)
                    return 0
                except Exception:
                    return 1
        else:
            try:
                test_connection = pool.getconn()
                pool.putconn(test_connection)
                return 0
            except Exception:
                return 1


pg_pool = postgre_pool()


class get_cursor:
    """
    creates and manages a cursor and its corresponding connection
    """
    global pg_pool

    def __init__(self, master_pool=pg_pool):
        """creates a cursor and a connection if a pool exists

        Keyword Arguments:
            master_pool {[postgre_pool]} -- [postgre_pool object to get the cursor from] (default: {pg_pool})
        """

        if master_pool:
            self.master_pool = master_pool
            self.connection = self.master_pool.pool.getconn()
            if self.connection:
                self.cursor = self.connection.cursor()
                return
            else:
                self.cursor = None
                print("Invalid pool supplied, aborting.")
        else:
            print("No valid pool, aborting.")

    def rollback(self):
        """rollback all changes made on this cursor's connection and close the connection
        """

        if self.connection:
            self.connection.rollback()
            self.connection.close()
        if self.cursor:
            self.cursor.close()
        self.master_pool.pool.putconn(self.connection)

    def commit(self):
        """"commits all changes done to the database and closes the connection
        """
        if self.connection:
            self.connection.commit()
            self.connection.close()
        if self.cursor:
            self.cursor.close()
        self.master_pool.pool.putconn(self.connection)


def create_dict_result(results, columns=COLUMNS):
    """creates dictionary column_key = value from the result of a select sql command

    Arguments:
        results {[list of tuples]} -- [result provided by the simple_sql_select (format ('one', 'two', ...))]

    Keyword Arguments:
        columns {[tuple]} -- [column names] (default: {COLUMNS})

    Returns:
        [array(dictionaries)] -- [result in array of dictionary where keys are column names]
    """

    dict_result = []
    for result in results:
        result_dictionary = {}
        for i in range(len(result)):
            result_dictionary[columns[i]] = result[i]
        dict_result.append(result_dictionary)
    return dict_result


def create_database_if_not_exists(database, user, host, port):
    """creates a database if it doesn't already exist

    Arguments:
        database {[string]} -- [database name]
        user {[string]} -- [username for db login] (default: {USER})
        host {[string]} -- [hostname for db login] (default: {HOST})
        port {[string]} -- [port for db login] (default: {PORT})
    """

    # creates a new connection
    connection = psycopg2.connect(
        user=user, host=host, port=port)
    connection.autocommit = True
    cursor = connection.cursor()
    sql_string = "SELECT COUNT(*) FROM pg_catalog.pg_database WHERE datname = '%s'" % database

    # checks if database exists
    cursor.execute(sql_string)
    count = cursor.fetchone()[0]

    # if it doesn't, create it
    if not count:
        print("Creating database '%s'" % database)
        sql_string = "CREATE DATABASE %s" % database
        cursor.execute(sql_string)
        # time.sleep(0.5)
        print("Database '%s' created!" % database)

    connection.close()


def create_default_table_if_not_exists(database, user, host, port):
    """creates a default table for the provided database

    Arguments:
        database {[string]} -- [database name]
        user {[string]} -- [username for db login] (default: {USER})
        host {[string]} -- [hostname for db login] (default: {HOST})
        port {[string]} -- [port for db login] (default: {PORT})
    """

    # creates a new connection
    connection = psycopg2.connect(
        user=user, host=host, port=port, database=database)
    connection.autocommit = True
    cursor = connection.cursor()
    table_name = AUTH_TABLE_NAME if database == AUTH_DB_NAME else DEFAULT_TABLE_NAME
    sql_string = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '%s')" % table_name
    # checks if table exists
    cursor.execute(sql_string)
    exists = cursor.fetchone()[0]

    # create a table if it doesn't exist
    if not exists:
        print("Creating table '%s'" % table_name)
        if database == AUTH_DB_NAME:
            sql_string = "CREATE TABLE %s (%s varchar(40) PRIMARY KEY, %s varchar(40))" % (
                table_name, AUTH_COLUMNS[0], AUTH_COLUMNS[1])
        else:
            sql_string = "CREATE TABLE %s (%s serial PRIMARY KEY, %s varchar(40) UNIQUE, %s integer, %s TIMESTAMP)" % (
                table_name, COLUMNS[0], COLUMNS[1], COLUMNS[2], COLUMNS[3])
        cursor.execute(sql_string)
        # time.sleep(0.5)
        print("Table '%s' created!" % AUTH_TABLE_NAME)

    connection.close()


def simple_sql_command(sql_string, cursor_wrapper=None, dispose=True):
    """sends a single sql command to the database, returns success/fail ONLY

    Arguments:
        sql_string {[string]} -- [sql command to be executed]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [get_cursor class (will create a new one if none is provided)] (default: {None})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [boolean] -- [False if completed, True if failed]
    """
    global pg_pool
    if cursor_wrapper:
        cursor = cursor_wrapper.cursor
    else:
        if pg_pool.check_pool() != 0:
            pg_pool.get_pool()
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
    """sends a single sql command to the database, returns SELECT result

    Arguments:
        sql_string {[string]} -- [sql command to be executed]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [get_cursor class (will create a new one if none is provided)] (default: {None})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [list of dictionaries OR True] -- [keys = column names, values = values in the row, each dictionary = one row OR 1 = Failed]
    """

    global pg_pool
    if cursor_wrapper:
        cursor = cursor_wrapper.cursor
    else:
        if pg_pool.check_pool() != 0:
            pg_pool.get_pool()
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
    if not i:
        return result
    return 1


def select_row(colname, colvalue, table_name, cursor_wrapper=None, dispose=True):
    """checks for a code in a table
    @out:


    Arguments:
        colname {[string]} -- [column to be searched]
        colvalue {[string]} -- [value to search for in the column]
        table_name {[string]} -- [table to search in]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new cursor wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [dicitionary OR True] -- [dictionary with row data, where keys are column names OR True if failed]
    """

    colvalue = str(colvalue)
    sql_string = "SELECT * FROM %s WHERE %s = '%s'" % (
        table_name, colname, colvalue)
    command_result = 1
    try:
        command_result = simple_sql_select(
            sql_string, cursor_wrapper, dispose)
        if command_result != 1:
            return create_dict_result(command_result)[0]
    except Exception as e:
        print(e)
    return command_result


def check_and_update_code(value, table_name, columns=COLUMNS, cursor_wrapper=None, dispose=True):
    """checks for a value in table (see select_row) and if found, updates its data (time last requested, number of requests) and returns data before the update

    Arguments:
        value {[string]} -- [value to update]
        table_name {[string]} -- [table to be updated]

    Keyword Arguments:
        columns {[tuple]} -- [column names to work with] (default: {COLUMNS})
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new cursor wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [list with one dictionary OR True] -- [list with data from the row before the update OR True if failed]
    """
    # check pool
    global pg_pool
    if pg_pool.check_pool() != 0:
        pg_pool.get_pool()
        while (pg_pool.check_pool() != 0):
            time.sleep(0.1)
    if not cursor_wrapper:
        cursor_wrapper = get_cursor()
    command_result = 1
    try:
        # check if the value is even in the table
        current_data = select_row(
            columns[1], value, table_name, cursor_wrapper, False)
        print(current_data)
        if current_data:
            # if yes, update it
            current_data["used"] = 0 if not current_data["used"] else current_data["used"]
            # increment used count, set time to current timestamp
            sql_string = "UPDATE %s SET %s=%s, %s='%s' WHERE %s='%s' " % (
                table_name, columns[2], current_data["used"] + 1, columns[3], datetime.now(), columns[1], value)
            command_result = simple_sql_command(
                sql_string, cursor_wrapper, dispose)
        else:
            # necessary to close the connection
            cursor_wrapper.commit()
            return 1
    except Exception as e:
        print(e)
    return 1 if command_result else current_data


def delete_entry(value, table_name, column_name, cursor_wrapper=None, dispose=True):
    """adds 1 or more entries to a table in the database

    Arguments:
        value {[string]} -- [value to delete]
        table_name {[string]} -- [name of the table to delete the value in]
        column_name {[string]} -- [name of the column to search the value in]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new cursor wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [boolean] -- [False if success else True]
    """
    sql_string = "DELETE FROM %s WHERE %s='%s'" % (
        table_name, column_name, value)
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def add_entries(values, table_name, cursor_wrapper=None, dispose=True, columns=COLUMNS):
    """adds 1 or more entries to a table in the database

    Arguments:
        values {[list]} -- [list of values to insert into the table (even for one, it must be an list)]
        table_name {[string]} -- [name of the table to be added into]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})
        columns {[tuple]} -- [column headers for the table] (default: {COLUMNS})

    Returns:
        [boolean] -- [False if success else True]
    """
    # create a sql insert string with all the values (format: ('value1'), ('value2'), ...)
    values_string = ""
    for i in range(len(values)):
        values_string += ("('" + values[i] + "')" +
                          ", " * (i != len(values) - 1))
    sql_string = "INSERT INTO %s (%s) VALUES %s" % (
        table_name, columns[1], values_string)
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def get_tables(cursor_wrapper=None, dispose=True):
    """returns a list of table names in the data database

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [list(strings) OR True] -- [list of all table names OR 1 = Failed]
    """

    sql_string = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    command_result = 1
    try:
        command_result = simple_sql_select(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    if command_result != 1:
        tables = []
        for table in command_result:
            tables.append(table[0])
    return tables


def clear_table(table_name, primary_column_name=COLUMNS[0], cursor_wrapper=None, dispose=True):
    """deletes everything in a table and resets the id (prim. key) indexing (if autoindexed)

    Arguments:
        table_name {[string]} -- [name of the table to be cleared]

    Keyword Arguments:
        primary_column_name {[string]} -- [name of the primary column] (default: {COLUMNS[0]})
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [boolean] -- [False if success else True]
    """

    global pg_pool
    if pg_pool.check_pool() != 0:
        pg_pool.get_pool()
        while (pg_pool.check_pool() != 0):
            time.sleep(0.1)
    if not cursor_wrapper:
        cursor_wrapper = get_cursor()
    # delete all entries and then set indexing of the primary key (ie. code_tickets_seq) to 1
    sql_string = "DELETE FROM %s" % table_name
    sql_string2 = "SELECT setval('%s_%s_seq', 1)" % (
        table_name, primary_column_name)
    command_result = 1
    try:
        # don't commit yet
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, False)
        if primary_column_name == COLUMNS[0]:
            # commit now
            simple_sql_command(
                sql_string2, cursor_wrapper, dispose)
        else:
            # or commit now
            if dispose:
                cursor_wrapper.commit()
    except Exception as e:
        print(e)
    return 1 if command_result else 0


def drop_table(table_name, cursor_wrapper=None, dispose=True):
    """drops a table

    Arguments:
        table_name {[string]} -- [name of the table to be dropped]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [boolean] -- [False if success else True]
    """

    sql_string = "DROP TABLE %s" % table_name
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def create_table(table_name, columns=COLUMNS, cursor_wrapper=None, dispose=True):
    """creates a table

    Arguments:
        table_name {[string]} -- [name of the table to be created]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})
        columns {[tuple]} -- [column headers for the table] (default: {COLUMNS})

    Returns:
        [boolean] -- [False if success else True]
    """

    sql_string = "CREATE TABLE %s (%s serial PRIMARY KEY, %s varchar(40) UNIQUE, %s integer, %s TIMESTAMP)" % (
        table_name, columns[0], columns[1], columns[2], columns[3])
    command_result = 1
    try:
        command_result = simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def export_table(table_name, columns=COLUMNS, cursor_wrapper=None, dispose=True):
    """exports all the codes in a table

    Arguments:
        table_name {[string]} -- [name of the table to export]

    Keyword Arguments:
        cursor_wrapper {[get_cursor]} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {[boolean]} -- [whether to dispose the cursor_wrapper after execution] (default: {True})

    Returns:
        [list of dictionaries OR True] -- [list of dictionaries, where dictionary is a single row, keys are column names OR True if failed]
    """

    if table_name in get_tables():
        sql_string = "SELECT * FROM %s" % table_name
        command_result = 1
        try:
            command_result = simple_sql_select(
                sql_string, cursor_wrapper, dispose)
        except Exception as e:
            print(e)
        if command_result != 1:
            return create_dict_result(command_result, columns)
        return command_result
    return 1


def rename_backups(index=0):
    """automatically renames backus to the pre-defined structure
    - shifts all backup indexes by one, deletes the oldest
    - backup_latest will be available for creation
    - do not change argument, it is for recursion only
    """
    # set filepath to path to the current file
    file_path = os.path.join(BACKUP_PATH, BACKUP_NAMES[index])
    if os.path.isfile(file_path):
        # if exists and is last, remove it
        if index == 9:
            os.remove(file_path)
        # else rename the next one (until the end) and rename current
        else:
            rename_backups(index + 1)
            os.rename(file_path,
                      os.path.join(BACKUP_PATH, BACKUP_NAMES[index + 1]))


def create_backup(scheduled=True, database=DB_NAME):
    """creates a predefined backup structure

    Keyword Arguments:
        scheduled {[boolean]} -- [if the backup is ran from a scheduler (True) or on request (False)] (default: {True})
        database {[string]} -- [name of the database to create the backup for] (default: {DB_NAME})

    Returns:
        [boolean] -- [False if success else True]
    """

    if scheduled:
        print("Starting scheduled '%s' database backup." % database)
    else:
        print("Starting requested '%s' database backup." % database)
    # make the latest backup unused
    rename_backups()
    try:
        # create backup_latest.gz file and write into it from pg_dump command (dumps the whole database)
        latest_file_path = os.path.join(
            BACKUP_PATH, "backup_latest_%s.gz" % database)
        with open(latest_file_path, "wb") as f:
            pg_dump('-h', HOST, '-U', USER, database, _out=f)
        print("Backup successful! @ %s" % time.strftime(
            "%a, %d %b %Y %H:%M:%S", time.gmtime()))
        return 0
    except Exception as e:
        print(e)
        return 1
