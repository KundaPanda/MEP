#!/usr/bin/python3

import db_handler as handler
import json
import os
from flask import Flask, request, render_template, abort, url_for, jsonify, Response, stream_with_context, send_from_directory
from random import randint, choice
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import string
import error_handler
import tempfile
from psycopg2 import pool
from time import sleep
from datetime import datetime

api = Flask(__name__, template_folder="templates", static_folder="static")
api.register_blueprint(error_handler.blueprint)
# pg_pool = handler.postgre_pool()
file_scheduler = None


CODE_LENGTH = 20
PUBLIC_PATH = os.path.abspath('public')

# TODO: class structure as well?


def get_random_code(length):
    """
    @in int length: length of the code to be generated
    @out int code: generated code
    """
    return randint(int("1" + "0" * (length - 1)), int("9" * length))


def get_random_filename():
    """
    @out str filename: random filename
    """
    return "".join(choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(randint(5, 21)))


def delete_file(afile, filename=None):
    """
    @in str afile: absolute path to the file to be deleted
    @in (optional) str filename: job_id (=filename) of the job to be removed (job calls this function upon execution to make sure it gets deleted after one successful removal)
    """
    try:
        os.remove(afile)
        if filename:
            file_scheduler.remove_job(filename)
        return 0
    except Exception as e:
        print(e)
        return 1


def delete_listener():
    """
    function to be called upon exit to close all the open file_scheduler jobs and shut it down
    do NOT call while running
    """
    global file_scheduler
    # tell all jobs to finish now
    for job in file_scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())
    # wait for jobs to finish, then kill scheduler
    while file_scheduler.get_jobs() != list():
        sleep(0.1)
    file_scheduler.shutdown()


def create_table(name, size, **kwargs):
    """
    @in str name: name of the table to be created
    @in int size: size of the table (number of rows)
    @out HTTP CODE
    """
    try:
        size = int(size)
    except Exception:
        return Response(status=406)
    result = handler.create_table(name)
    if not result:
        result = add_entries(name, size)
        return result
    return Response(status=304)


def delete_table(name, **kwargs):
    """
    @in str name: name of the table to be deleted
    @out HTTP CODE
    deletes a table in the database
    """
    result = handler.drop_table(name)
    return Response(status=200) if not result else Response(status=304)


def clear_table(name, **kwargs):
    """
    @in str name: name of the table to be deleted
    @out HTTP CODE
    clears and resets a table in the database
    """
    result = handler.clear_table(name)
    return Response(status=200) if not result else Response(status=304)


def backup_db(**kwargs):
    """
    @out link to database in gz format
    backs up the database and returns dl link for the user (after 10 minuets, temp file will be deleted)
    """
    global file_scheduler
    response = handler.create_backup(False)
    temporary_file_name = get_random_filename() + ".gz"
    if temporary_file_name in os.walk(PUBLIC_PATH):
        while temporary_file_name in os.walk(PUBLIC_PATH):
            temporary_file_name = get_random_filename() + ".gz"

    temporary_file_path = os.path.join(PUBLIC_PATH, temporary_file_name)

    with open(temporary_file_path, "wb") as temp_file:
        with open(os.path.join(os.path.abspath("backups"), "backup_latest.gz"), "rb") as backup_file:
            temp_file.writelines(backup_file.readlines())

    file_scheduler.add_job(delete_file, args=(temporary_file_path, temporary_file_name),
                           id=temporary_file_name, trigger='interval', minutes=10)

    if response:
        return Response(status=500)
    else:
        result = get_file(temporary_file_name)
        print(result)
        return result


def restore_db(filepath, **kwargs):
    """
    @in str filepath: gz backup file path
    @out HTTP CODE
    restores the database from the provided gz backup
    """
    # TODO
    return Response(status=200)


def add_entries(name, size, **kwargs):
    """
    @in str name: name of the table to be inserted into
    @in int size: number of rows to be added
    @out HTTP CODE
    """
    # TODO: add checking if already in db
    try:
        size = int(size)
        if size < 0:
            return Response(status=400)
        name = str(name)
    except Exception as e:
        print(e)
        return Response(status=417)
    try:
        codes = []
        while len(codes) < size:
            code = "('" + str(get_random_code(CODE_LENGTH)) + "')"
            if code not in codes:
                codes.append(code)
        result = handler.add_entries(codes, name)
        return Response(status=200) if not result else Response(status=304)
    except pool.PoolError as f:
        print(f)
        handler.pg_pool.close_pool()
        return Response(status=500)
    except Exception as e:
        print(e)
        return Response(status=500)


def select_code(name, code, **kwargs):
    """
    @in str name: name of the table to be searched
    @in str code: code to be searched for
    @out: json object containing the row with the code
    selects a row in a table and returns the row as a json
    """
    result = handler.select_code(code, name)
    if result:
        return jsonify(result), 200
    else:
        return Response(status=418)


def update_code(name, code, **kwargs):
    """
    @in str name: name of the table to be modified
    @in str code: code to be updated (upon being scanned)
    @out: HTTP CODE
    updates a row with the provided code in the selected table
    """
    result = handler.check_and_update_code(code, name)
    if result != 1:
        return jsonify(result), 200
    else:
        return Response(status=304)


methods_ui = {
    "create_table": create_table,
    "delete_table": delete_table,
    "clear_table": clear_table,
    "backup_db": backup_db,
    "restore_db": restore_db,
    "add_entries": add_entries,
    "select_code": select_code,
    "update_code": update_code,
}

methods_client = {
    "update_code": update_code,

}

parameter_names = {
    "create_table": ["name", "size"],
    "delete_table": ["name"],
    "clear_table": ["name"],
    "backup_db": [],
    "restore_db": ["data"],
    "add_entries": ["name", "size"],
    "select_code": ["name", "code"],
    "update_code": ["name", "code"],
}

parameters = {"name": "", "size": "", "data": "", "code": ""}


@api.route("/api/ui/<method>", methods=["POST"])
def ui(method):
    """
    route for all ui (web interface) calls
    """
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    if method in methods_ui.keys():
        for parameter in parameter_names[method]:
            if parameter not in post_data:
                abort(400)
            parameters[parameter] = post_data[parameter]
        return (methods_ui[method](**parameters))
    else:
        abort(405)


@api.route("/api/client/<method>", methods=["POST"])
def client(method):
    """
    route for all client calls
    """
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    if method in methods_client.keys():
        for parameter in parameter_names[method]:
            if parameter not in post_data:
                abort(400)
            parameters[parameter] = post_data[parameter]
        return (methods_client[method](**parameters))
    else:
        abort(405)


@api.route("/public/<filename>")
def get_file(filename):
    """
    route for file download (public folder)
    """
    filepath = os.path.join(PUBLIC_PATH, filename)
    if not os.path.isfile(filepath):
        return Response(status=404)
    with open(filepath, "rb") as afile:
        result = Response(afile.read())
    result.headers["Content-Encoding"] = 'gzip'
    result.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    result.headers["Content-type"] = "text/csv"
    return result


if __name__ == "__main__":
    # start file deletion scheduler and backup scheduler, then create a pool and start the api
    file_scheduler = BackgroundScheduler()
    file_scheduler.start()
    scheduler = BackgroundScheduler()
    scheduler.add_job(handler.create_backup,
                      id="backup_scheduler", trigger='interval', hours=1)
    scheduler.start()
    atexit.register(delete_listener)
    atexit.register(scheduler.shutdown)
    handler.pg_pool.get_pool()
    # handler.clear_table("tickets")
    api.run(debug=True, port=5000, use_reloader=False)
