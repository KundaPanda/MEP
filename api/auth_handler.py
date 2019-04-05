#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def pool_init():
    global pg_pool
    pg_pool.get_pool(
        maxconn=POOL_SIZE, user=USER, database=DB_NAME, port=PORT, host=HOST)


def add_users(users,
              table,
              cursor_wrapper=None,
              dispose=True,
              users_column=COLUMNS[0],
              tables_column=COLUMNS[1]):
    """adds users to users database and assigns them the specified table

    Arguments:
        users {list} -- [list of users to insert into the table (even for one, it must be a list)]
        table {string} -- [name of the table to add to these users]

    Keyword Arguments:
        cursor_wrapper {db_handler.get_cursor} -- [cursor wrapper to be executed with (for multiple actions with a single cursor)] (default: {new wrapper})
        dispose {boolean} -- [whether to dispose the cursor_wrapper after execution] (default: {True})
        users_column {string} -- [name of the column usernames are stored in] (default: {COLUMNS[0]})
        tables_column {string} -- [name of the column table names are stored in] (default: {COLUMNS[1]})

    Returns:
        [boolean] -- [False if successful else True]
    """

    # create a new wrapper
    if not cursor_wrapper:
        cursor_wrapper = db_handler.get_cursor(pg_pool)
    # create string with values (user:table (ie. (('user'), ('table')), ...))
    values_string = ""
    for i in range(len(users)):
        values_string += "("
        values_string += ("('" + users[i] + "')" + ", ")
        values_string += ("('" + table + "')")
        values_string += ")" + ", " * (i != len(users) - 1)

    # insert all values
    sql_string = "INSERT INTO %s (%s, %s) VALUES %s" % (
        TABLE_NAME, users_column, tables_column, values_string)
    command_result = 1
    try:
        command_result = db_handler.simple_sql_command(sql_string,
                                                       cursor_wrapper, dispose)
    except Exception as e:
        print(e)
    return command_result


def find_corresponding_table(user):
    """finds the table the user is assigned to

    Arguments:
        user {[string]} -- [username]

    Returns:
        [boolean] -- [False if successful else True]
    """

    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.select_row(COLUMNS[0], user, TABLE_NAME,
                                   cursor_wrapper, True)
    if result != 1:
        return {"table_name": result[db_handler.COLUMNS[1]]}
    else:
        return 1


def delete_all_users():
    """deletes all users in the users database

    Returns:
        [boolean] -- [False if successful else True]
    """

    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.clear_table(TABLE_NAME, COLUMNS[0], cursor_wrapper)
    return result


def delete_all_users_for_table(table_name):
    """deletes all users assigned to the selected table

    Returns:
        [boolean] -- [False if successful else True]
    """
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    result = db_handler.delete_entry(table_name, TABLE_NAME, COLUMNS[1],
                                     cursor_wrapper)
    return result
