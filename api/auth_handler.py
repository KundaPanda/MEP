#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import db_handler

# TODO

POOL_SIZE = 50
COLUMNS = db_handler.AUTH_COLUMNS
USER = db_handler.USER
DB_NAME = db_handler.AUTH_DB_NAME
PORT = db_handler.PORT
HOST = db_handler.HOST
TABLE_NAME = db_handler.AUTH_TABLE_NAME

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
        cursor_wrapper {db_handler.get_cursor} -- [cursor wrapper to be executed with (for multiple actions with
            a single cursor)] (default: {new wrapper})
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


def reassign_users(users, table_name):
    """reassigns list of users to a different table

    Arguments:
        users {[list]} -- [usernames to be reassigned]
        table_name {[string]} -- [name of the target table]

    Returns:
        [Boolean] -- [True if failed, False if OK]
    """
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    tables = db_handler.get_tables(cursor_wrapper, False)
    if table_name not in tables:
        return True
    response = False
    for user in users:
        command = "UPDATE %s SET %s='%s' WHERE %s='%s'" % (
            db_handler.AUTH_TABLE_NAME, db_handler.AUTH_COLUMNS[1], table_name,
            db_handler.AUTH_COLUMNS[0], user)
        response ^= db_handler.simple_sql_select(command, cursor_wrapper)
    return response


def delete_users(users):
    """deletes multiple users from assignment table

    Arguments:
        users {[list]} -- [users to be removed]

    Returns:
        [Boolean] -- [True if failed, else False]
    """
    cursor_wrapper = db_handler.get_cursor(pg_pool)
    response = False
    for user in users:
        response ^= db_handler.delete_entry(user, TABLE_NAME, COLUMNS[0])
    return response
