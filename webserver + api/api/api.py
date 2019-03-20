#!C:/Users/vojdo/AppData/Local/Programs/Python/Python37/python.exe

# import sys
# import hashlib
import db_handler as handler
import json
import os
from flask import Flask, request, render_template, abort, url_for, jsonify, Response, stream_with_context
from random import randint

# from time import time

api = Flask(__name__, template_folder="templates", static_folder="static")
postgre_pool = None
# auth_database_path = "../databases/auth.db"
# sql_worker = Sqlite3Worker(auth_database_path)


CODE_LENGTH = 20


@api.errorhandler(400)
def bad_request(dump):
    return (
        render_template(
            "index.html",
            body="400 Bad request",
            image=url_for("static", filename="400.jpg"),
        ),
        400,
    )


@api.errorhandler(401)
def unauthorized(dump):
    return (
        render_template(
            "index.html",
            body="401 Unauthorized",
            image=url_for("static", filename="/401.jpg"),
        ),
        401,
    )


@api.errorhandler(403)
def forbidden(dump):
    return (
        render_template(
            "index.html",
            body="403 Forbidden",
            image=url_for("static", filename="403.jpg"),
        ),
        403,
    )


@api.errorhandler(404)
def not_found(dump):
    return (
        render_template(
            "index.html",
            body="404 Not found",
            image=url_for("static", filename="404.jpg"),
        ),
        404,
    )


@api.errorhandler(405)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="405 Method not allowed",
            image=url_for("static", filename="405.jpg"),
        ),
        405,
    )


@api.errorhandler(417)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="417 Expectation failed",
            image=url_for("static", filename="417.jpg"),
        ),
        417,
    )


@api.errorhandler(500)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="500 Internal server error",
            image=url_for("static", filename="500.jpg"),
        ),
        500,
    )


def get_random_code(length):
    return randint(int("1" + "0" * (length - 1)), int("9" * length))


def create_table(name, size, **kwargs):
    """
    @in name: name of the table to be created
    @in size: size of the table (number of rows)
    @out HTTP CODE
    """
    return Response(status=200)


def delete_table(name, **kwargs):
    """
    @in name: name of the table to be deleted
    @out HTTP CODE
    """
    return Response(status=200)


def backup_db(**kwargs):
    """
    @out database table in json
    """
    database = json.loads(json.dumps({"name": "name", "data": "data"}))
    return jsonify(name="TEST", data=database), 200


def restore_db(data, **kwargs):
    """
    @in data: json-formatted database table
    @out HTTP CODE
    """
    return Response(status=200)


def add_entries(name, size, **kwargs):
    """
    @in name: name of the table to be inserted into
    @in size: number of rows to be added
    @out HTTP CODE
    """
    try:
        size = int(size)
        name = str(name)
    except Exception as e:
        print(e)
        return Response(status=417)
    try:
        for i in range(size):
            code = str(get_random_code(CODE_LENGTH))
            result = handler.add_entry(code, name)
            while result:
                code = str(get_random_code(CODE_LENGTH))
                result = handler.add_entry(code, name)
        return Response(status=200)
    except Exception as e:
        print(e)
        return Response(status=500)


def select_code(name, code, **kwargs):
    result = handler.select_code(code, name)
    if result:
        return jsonify(result), 200
    else:
        return jsonify(None), 200


methods_ui = {
    "create_table": create_table,
    "delete_table": delete_table,
    "backup_db": backup_db,
    "restore_db": restore_db,
    "add_entries": add_entries,
    "select_code": select_code,
}


parameter_names = {
    "create_table": ["name", "size"],
    "delete_table": ["name"],
    "backup_db": [],
    "restore_db": ["data"],
    "add_entries": ["name", "size"],
    "select_code": ["name", "code"],
}

parameters = {"name": "", "size": "", "data": "", "code": ""}


@api.route("/api/ui/<method>", methods=["POST"])
def client(method):
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    if method in methods_ui.keys():
        for parameter in parameter_names[method]:
            if parameter not in post_data:
                print(post_data, parameter)
                abort(400)
            parameters[parameter] = post_data[parameter]
        return (methods_ui[method](**parameters))
    else:
        abort(405)


@api.route("/api/client")
def ui():
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    return "Hello from client API!. Received: %s" % post_data


if __name__ == "__main__":
    handler.get_pool()
    # handler.clear_table("tickets")
    api.run(debug=True, port=5000)
