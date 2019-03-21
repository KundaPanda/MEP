#!/usr/bin/python3

import db_handler

# TODO

POOL_SIZE = 100
COLUMNS = ("username", "tablename")
USER = "postgres"
DB_NAME = "users"
PORT = "5432"
HOST = "localhost"
TABLE_NAME = "users"


db_handler.AUTH_COLUMNS = COLUMNS
db_handler.AUTH_DB_NAME = DB_NAME
db_handler.AUTH_TABLE_NAME = TABLE_NAME


pg_pool = db_handler.postgre_pool()


def get_pool_init():
    global pg_pool
    pg_pool.get_pool(maxconn=POOL_SIZE, user=USER,
                     database=DB_NAME, port=PORT, host=HOST)


def add_users(users, table, cursor_wrapper=None, dispose=True, users_column=COLUMNS[0], tables_column=COLUMNS[1]):
    """
    @in array users: array of users to insert into the table (even for one, it must be an array)
    @in str talbe: name of the table to add to these users
    @in (optional) get_cursor cursor_wrapper: cursor wrapper to be executed with (for multiple actions with a single cursor)
    @in (optional) bool dispose: whether to dispose the cursor_wrapper after execution
    @in (optional) str users_column: name of the column usernames are stored in
    @in (optional) str tables_column: name of the column table names are stored in
    @out: 0 if success else 1
    adds 1 or more entries to a table in the database
    """
    if not cursor_wrapper:
        cursor_wrapper = db_handler.get_cursor(pg_pool)
    values_string = ""
    for i in range(len(users)):
        values_string += "("
        values_string += ("('" + users[i] + "')" +
                          ", ")
        values_string += ("('" + table + "')")
        values_string += ")" + ", " * (i != len(users) - 1)

    sql_string = "INSERT INTO %s (%s, %s) VALUES %s" % (
        TABLE_NAME, users_column, tables_column, values_string)
    command_result = 1
    try:
        command_result = db_handler.simple_sql_command(
            sql_string, cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def find_corresponding_table(user):
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.select_row(
        COLUMNS[0], user, TABLE_NAME, cursor_wrapper, True)
    if result != 1:
        return result[1][0]
    else:
        print("USER NOT IN DATABASE")
        return 1

# TODO: documentation


def delete_all_users():
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.clear_table(TABLE_NAME, COLUMNS[0], cursor_wrapper)
    return result


def delete_all_users_for_table(name):
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.delete_entry(
        name, TABLE_NAME, COLUMNS[1], cursor_wrapper)
    return result