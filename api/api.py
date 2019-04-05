#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import db_handler as handler
import json
import os
from flask import Flask, request, render_template, abort, url_for, jsonify, Response, stream_with_context, send_from_directory
from flask_basicauth import BasicAuth
from random import randint, choice
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import string
import tempfile
from psycopg2 import pool
from time import sleep
from datetime import datetime
import logging
import logging.handlers
import auth_handler
import tickets
import base64

# initialize the global api and file_scheduler variables
api = Flask(__name__, template_folder="templates", static_folder="static")
file_scheduler = None

LOGGING_TO_FILE = False

# columns - (primary id key, code itself, number of times userd, time used)
COLUMNS = ("id", "code", "used", "time")
# pre-defined code length for uniformity
CODE_LENGTH = 20
PUBLIC_PATH = os.path.abspath('public')

# TODO: class structure as well?


def get_random_code(length):
    """generates a radnom int code with the predefined length

    Arguments:
        length {[integer]} -- [desired code length]

    Returns:
        [integer] -- [generated code]
    """

    return randint(int("1" + "0" * (length - 1)), int("9" * length))


def get_random_filename():
    """creates a random filename from all letters and numbers

    Returns:
        [string] -- [generated filename]
    """

    return "".join(
        choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(randint(5, 21)))


def delete_file(afile, filename=None):
    """deletes a file and its job (if id is provided)

    Arguments:
        afile {[string]} -- [absolute path to the file to be deleted]

    Keyword Arguments:
        filename {[string]} -- [job_id (=filename) of the job to be removed (job calls this function upon execution to make sure it gets deleted after one successful removal)] (default: {None})

    Returns:
        [boolean] -- [False if successful else True]
    """

    try:
        os.remove(afile)
        if filename:
            file_scheduler.remove_job(filename)
        return 0
    except Exception as e:
        print(e)
        return 1


def delete_listener(ascheduler):
    """
    function to be called upon exit to close all the open file_scheduler jobs and shut it down
    do NOT call while running
    """
    # tell all jobs to finish now
    for job in ascheduler.get_jobs():
        job.modify(next_run_time=datetime.now())
    # wait for jobs to finish, then kill scheduler
    while ascheduler.get_jobs() != list():
        sleep(0.1)
    ascheduler.shutdown()


def create_table(table_name, size=0, **kwargs):
    """creates a table

    Arguments:
        table_name {[string]} -- [name of the table to be created]
        size {[string / integer]} -- [size of the table (number of rows)]

    Returns:
        [Response] -- [HTTP response code]
    """

    # check if name and size are valid
    try:
        size = int(size)
    except Exception:
        return Response(status=406)
    if table_name and size:
        # get all table names of the database and check if the table is already in the database
        tables = handler.get_tables()
        # if not in database, add it
        if table_name not in tables:
            result = handler.create_table(table_name)
            if not result:
                result = Response(status=201)
                if size > 0:
                    result = add_entries(table_name, size)
                return result
    return Response(status=304)


def delete_table(table_name, **kwargs):
    """deletes a table

    Arguments:
        table_name {[string]} -- [name of the table to be deleted]

    Returns:
        [Response] -- [HTTP response code]
    """
    result = handler.drop_table(table_name)
    return Response(status=200) if not result else Response(status=304)


def clear_table(table_name, **kwargs):
    """resets a table

    Arguments:
        table_name {[string]} -- [name of the table to be cleared]

    Returns:
        [Response] -- [HTTP response code]
    """
    result = handler.clear_table(table_name)
    return Response(status=200) if not result else Response(status=304)


def backup_db(**kwargs):
    """backs up the database and returns dl link for the user (after 10 minuets, temp file will be deleted)

    Returns:
        [Response (+ string)] -- [HTTP response code + relative path to the backup file if successful]
    """

    global file_scheduler
    # create a backup and a random file
    response = handler.create_backup(False)
    temporary_file_name = get_random_filename() + ".gz"
    if temporary_file_name in os.walk(PUBLIC_PATH):
        while temporary_file_name in os.walk(PUBLIC_PATH):
            temporary_file_name = get_random_filename() + ".gz"

    # move the random file to the public folder
    temporary_file_path = os.path.join(PUBLIC_PATH, temporary_file_name)

    # copy all the data from the backup to the new file
    with open(temporary_file_path, "wb") as temp_file:
        with open(
                os.path.join(
                    os.path.abspath("backups"),
                    "backup_latest_%s.gz" % handler.DB_NAME),
                "rb") as backup_file:
            temp_file.writelines(backup_file.readlines())

    # add a job to the file scheduler to delete the file after 10 minutes
    file_scheduler.add_job(
        delete_file,
        args=(temporary_file_path, temporary_file_name),
        id=temporary_file_name,
        trigger='interval',
        minutes=10)

    if response:
        return Response(status=500)
    else:
        # return a download link to the file
        return jsonify(os.path.relpath(temporary_file_path)), 200


def restore_db(filepath, **kwargs):
    # TODO documentation after implementation
    """restores the database from the provided gz backup

    Arguments:
        filepath {[string]} -- [path to the backup file]

    Returns:
        [Response] -- [HTTP response code]
    """

    # TODO implementation
    return Response(status=201)


def add_entries(table_name, size, **kwargs):
    """adds one or more entries to a table

    Arguments:
        table_name {[string]} -- [name of the table to be inserted into]
        size {[string / integer]} -- [number of rows to be added]

    Returns:
        [Response] -- [HTTP response code]
    """

    # check if table_name and size valid
    try:
        size = int(size)
        if size < 0:
            return Response(status=400)
        elif size == 0:
            return Response(status=200)
        table_name = str(table_name)
    except Exception as e:
        print(e)
        return Response(status=417)
    if table_name and size:
        try:
            # create a list of unique codes (check if they are in the table already)
            codes = []
            result = 1
            cursor_wrapper = handler.get_cursor()
            while len(codes) < size:
                code = str(get_random_code(CODE_LENGTH))
                # create a new code if the old one is in the table already
                while ((code in codes) and (not handler.select_row(
                        handler.COLUMNS[1], code, table_name, cursor_wrapper,
                        False))):
                    code = str(get_random_code(CODE_LENGTH))
                codes.append(code)
            if codes != []:
                # insert codes into the table
                result = handler.add_entries(codes, table_name, cursor_wrapper,
                                             True)
            return Response(status=201) if not result else Response(status=304)
        except pool.PoolError as f:
            print(f)
            return Response(status=500)
        except Exception as e:
            print(e)
            return Response(status=304)
    return Response(status=400)


def select_code(table_name, code, **kwargs):
    """selects a row in a table and returns the row as a json

    Arguments:
        code {[string]} -- [code to look for]
        table_name {[string]} -- [name of the table to be searched]

    Returns:
        [json OR Response] -- [json with row containing the code and HTTP response code OR HTTP response code]
    """

    if not table_name or not code:
        return Response(status=400)
    result = handler.select_row("code", code, table_name)
    if result:
        return jsonify(result), 200
    else:
        return Response(status=418)


def update_code(table_name, code, **kwargs):
    """updates a row with the provided code in the selected table

    Arguments:
        code {[string]} -- [code to update]
        table_name {[string]} -- [name of the table to be searched]

    Returns:
        [json OR Response] -- [json with row containing the code before modifiaction and HTTP response code OR HTTP response code]
    """

    if not table_name or not code:
        return Response(status=400)
    result = handler.check_and_update_code(code, table_name)
    if result != 1:
        return jsonify(result), 200
    else:
        return Response(status=304)


def add_users(table_name, users, **kwargs):
    """assigns all users from provided list to the selected table (adds them to users database)

    Arguments:
        users {[list]} -- [list of users to add to users database]
        table_name {[string]} -- [name of the table to assign these users to]

    Returns:
        [Response] -- [HTTP response code]
    """

    result = 1
    if (not isinstance(users, list)):
        users = [users]
    # check if users and table_name exist
    if isinstance(users, list) and table_name:
        result = handler.get_tables()
        # check if the specified table exists
        if table_name in result:
            # if yes, then add users assigned to this table
            result = auth_handler.add_users(users, table_name)
            if result == 1:
                return Response(status=304)
        else:
            result = 1
    return Response(status=400) if (result == 1) else Response(status=200)


def delete_all_users(**kwargs):
    """deletes all users no matter the table they are assigned to

    Returns:
        [Response] -- [HTTP response code]
    """

    result = 1
    try:
        result = auth_handler.delete_all_users()
    except Exception:
        pass
    return Response(status=304) if (result == 1) else Response(status=200)


def delete_users_for_table(table_name, **kwargs):
    """deletes all users assigned to a specific table

    Arguments:
        table_name {[string]} -- [name of the table which users to delete]

    Returns:
        [Response] -- [HTTP response code]
    """

    result = 1
    try:
        result = auth_handler.delete_all_users_for_table(table_name)
    except Exception:
        pass
    return Response(status=304) if (result == 1) else Response(status=200)


def assigned_user_table(user, **kwargs):
    """finds the table that the user is assigned to

    Arguments:
        user {[string]} -- [username for which to find the assigned table]

    Returns:
        [string OR boolean] -- [name of the table the user is assigned to OR True if unassigned (or other error)]
    """

    result = 1
    try:
        result = auth_handler.find_corresponding_table(user)
    except Exception as e:
        print(e)
    return Response(status=400) if result else (jsonify(result), 200)


def export_tickets(table_name, file_format, per_page, **kwargs):
    codes = []
    result_list = handler.export_table(table_name)
    if result_list == 1 or type(result_list) != list:
        return Response(status=400)
    result_list = sorted(result_list, key=lambda k: k["id"])
    for dictionary in result_list:
        codes.append(dictionary[handler.COLUMNS[1]])
    filename = tickets.export_codes(codes)
    return jsonify(filename), 200


# methods that can be called from /api/ui/<method>
methods_ui = {
    "create_table": create_table,
    "delete_table": delete_table,
    "clear_table": clear_table,
    "backup_db": backup_db,
    "restore_db": restore_db,
    "add_entries": add_entries,
    "select_code": select_code,
    "update_code": update_code,
    "add_users": add_users,
    "delete_all_users": delete_all_users,
    "delete_users_for_table": delete_users_for_table,
    "assigned_user_table": assigned_user_table,
    "export_tickets": export_tickets,
}

# parameters required by each method
# TODO Maybe pass whole parameters dictionary and get the desired values from there?
parameter_names = {
    "create_table": ["table_name", "size"],
    "delete_table": ["table_name"],
    "clear_table": ["table_name"],
    "backup_db": [],
    "restore_db": ["data"],
    "add_entries": ["table_name", "size"],
    "select_code": ["table_name", "code"],
    "update_code": ["table_name", "code"],
    "add_users": ["users", "table_name"],
    "delete_all_users": [],
    "delete_users_for_table": ["table_name"],
    "assigned_user_table": ["user"],
    "export_tickets": ["table_name", "file_format", "per_page"]
}

parameters = {
    "table_name": "",
    "size": "",
    "data": "",
    "code": "",
    "users": "",
    "user": "",
    "file_format": "",
    "per_page": ""
}

optional_parameters = {"file_format": "html", "per_page": 8}


@api.route("/api/ui/<method>", methods=["POST"])
def ui(method):
    """route for all ui (web interface) calls

    Arguments:
        method {[string]} -- [which method should be called]

    Returns:
        [Response OR Json and Response] -- [HTTP response code OR json with data and HTTP response code]
    """

    # read json post body
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    # check if all required fields are filled and call the function
    if method in methods_ui.keys():
        for parameter in parameter_names[method]:
            if parameter not in post_data:
                # check if parameter is not optional
                if parameter in optional_parameters.keys():
                    parameters[parameter] = optional_parameters[parameter]
                    continue
                else:
                    abort(400)
            parameters[parameter] = str(post_data[parameter])
        return (methods_ui[method](**parameters))
    else:
        abort(405)


@api.route("/api/client/check_login", methods=["POST"])
def check_login(**kwargs):
    try:
        user = request.headers["Authorization"].replace("Basic ", "")
        user = base64.b64decode(user).decode('utf-8').split(":")[0]
        table_name = assigned_user_table(user)
        if table_name == 1:
            return Response(status="401")
        return Response(status="200")
    except Exception as e:
        print(e)
        return Response(status="401")


@api.route("/api/client", methods=["POST"])
def client(**kwargs):
    """route for all client (mobile app) calls

    Arguments:
        method {[string]} -- [which method should be called]

    Returns:
        [Response OR Json and Response] -- [HTTP response code OR json with data and HTTP response code]
    """
    # rear input json and initialize table_name for the user
    method = "update_code"
    try:
        post_data = str(request.get_json()).replace("\'", "\"")
        post_data = json.loads(post_data)
        post_data['table_name'] = None
    except Exception as e:
        print(e)
        abort(400)

    # check if all required fields are filled
    for parameter in parameter_names[method]:
        if parameter not in post_data:
            print("Not enough parameters")
            abort(400)
        parameters[parameter] = post_data[parameter]
    # find the assigned table, abort if no assignment is found else call the method
    user = request.headers["Authorization"].replace("Basic ", "")
    user = base64.b64decode(user).decode('utf-8').split(":")[0]
    table_name = assigned_user_table(user)
    if table_name == 1:
        return Response(status=401)
    parameters["table_name"] = table_name
    return (update_code(**parameters))


@api.route("/public/<filename>")
def get_file(filename):
    """route for file download (public folder)

    Arguments:
        filename {[string]} -- [name of the file to download, must include extension]

    Returns:
        [Response OR Attachment] -- [HTTP response code OR attachment containing the file]
    """

    # return file as an attachement if exists
    filepath = os.path.join(PUBLIC_PATH, filename)
    if not os.path.isfile(filepath):
        return Response(status=404)
    with open(filepath, "rb") as afile:
        result = Response(afile.read())
    result_split = result.split(".")
    if (len(result_split) < 2):
        return Response(status=400)
    if (result_split[-1] == "gz"):
        encoding = "gzip"
        content_type = "text/csv"
    else:
        encoding = "identity"
        content_type = "text/html; charset=utf-8"
    result.headers["Content-Encoding"] = encoding
    result.headers[
        "Content-Disposition"] = "attachment; filename=%s" % filename
    result.headers["Content-type"] = content_type
    return result


if __name__ == "__main__":
    # start file deletion scheduler and backup scheduler, then create a pool and start the api
    print("----------INIT----------")
    file_scheduler = BackgroundScheduler()
    file_scheduler.start()
    print("Started file scheduler.")

    tickets_backup_scheduler = BackgroundScheduler()
    tickets_backup_scheduler.add_job(
        handler.create_backup,
        args=[True, handler.DB_NAME],
        id="tickets_backup_scheduler",
        trigger='interval',
        hours=1)
    tickets_backup_scheduler.start()
    print("Started tickets backup scheduler.")

    users_backup_scheduler = BackgroundScheduler()
    users_backup_scheduler.add_job(
        handler.create_backup,
        args=[True, auth_handler.DB_NAME],
        id="users_backup_scheduler",
        trigger='interval',
        hours=1)
    users_backup_scheduler.start()
    print("Started users backup scheduler.")

    # at exit, finish all schedulers
    atexit.register(delete_listener, file_scheduler)
    atexit.register(tickets_backup_scheduler.shutdown)
    atexit.register(users_backup_scheduler.shutdown)

    # create pools for both handlers
    handler.pg_pool.get_pool()
    auth_handler.pool_init()

    # if logging is true, log everything to api_log.log
    if LOGGING_TO_FILE:
        logging_handler = logging.handlers.RotatingFileHandler(
            filename="api_log.log",
            maxBytes=(1024 * 1024),
        )
        logging_handler.setLevel(logging.DEBUG)
        api.logger.addHandler(logging_handler)
        werkzeug_logger = logging.getLogger("werkzeug")
        werkzeug_logger.setLevel(logging.DEBUG)
        werkzeug_logger.addHandler(logging_handler)
    print("----------INIT----------")

    # start the server

    basic_auth = BasicAuth(api)
    api.run(debug=True, port=5000, use_reloader=False, host="0.0.0.0")
