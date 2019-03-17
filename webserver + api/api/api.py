#!C:/Users/vojdo/AppData/Local/Programs/Python/Python37/python.exe

# import db_handler
# from sqlite3worker import Sqlite3Worker
# import json
# import sys
import os

# import hashlib
from flask import Flask, request, render_template, abort, url_for

# from time import time

api = Flask(__name__, template_folder="templates", static_folder="static")
# auth_database_path = "../databases/auth.db"
# sql_worker = Sqlite3Worker(auth_database_path)

# auth_table_name = "auth"


def create_db(name, size, **kwargs):
    """
    @in name: name of the database and table to be created
    @in size: size of the table (number of rows)
    @out HTTP CODE
    """
    print("create_db")


def delete_db(name, **kwargs):
    """
    @in name: name of the database and table to be deleted
    @out HTTP CODE
    """
    print("delete_db")


def backup_db(name, **kwargs):
    """
    @in name: name of the database and table to be backed up
    @out database table in json
    """
    print("backup_db")


def restore_db(name, data, **kwargs):
    """
    @in name: name of the database and table to be restored
    @in data: json-formatted database table
    @out HTTP CODE
    """
    print("restore_db")


def add_entries(name, size, **kwargs):
    """
    @in name: name of the database and table to be inserted into
    @in size: number of rows to be added
    @out HTTP CODE
    """
    print("add_entries")


methods_ui = {
    "create_db": create_db,
    "delete_db": delete_db,
    "backup_db": backup_db,
    "restore_db": restore_db,
    "add_entries": add_entries,
}


parameter_names = {
    "create_db": ("name", "size"),
    "delete_db": ("name"),
    "backup_db": ("name"),
    "restore_db": ("name", "data"),
    "add_entries": ("name", "size"),
}

parameters = {"name": "", "size": "", "data": ""}


def image_path(image):
    return os.path.abspath(os.path.join(api.static_folder, image))


@api.route("/")
def hello_world():
    return "Hello World!"


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


@api.route("/api/ui/<method>", methods=["POST"])
def client(method):
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    for parameter in parameter_names[method]:
        if parameter not in post_data:
            abort(400)
        parameters[parameter] = post_data[parameter]
    methods_ui[method](**parameters)
    return "Hello from UI API!. Received: %s" % post_data


@api.route("/api/client")
def ui():
    try:
        post_data = request.get_json()
    except Exception:
        abort(400)

    return "Hello from client API!. Received: %s" % post_data


if __name__ == "__main__":
    api.run(debug=True, port=5000)


# def authenticated(commands):
#     response = cherrypy.response
#     response.status = "200 OK"
#     result = db_handler.get_commands(commands)
#     return result


# def removekey(d, key):
#     r = dict(d)
#     del r[key]
#     return r


# def authenticate(data):
#     if "username" in data and "password" in data:
#         username = data["username"]
#         password = data["password"]
#         password = hashlib.sha3_256(password.encode("UTF-8")).hexdigest()

#         countt = sql_worker.execute(
#             'SELECT COUNT(password) FROM {} WHERE username="{}" AND password="{}"'.format(
#                 auth_table_name, username, password
#             )
#         )
#         countt = countt[0][0]
#         if countt == 1:

#             commands = removekey(data, "username")
#             del commands["password"]

#             result = authenticated(commands)

#             return result
#         else:
#             raise cherrypy.HTTPError(401, "Bad login credentials")
#     else:
#         raise cherrypy.HTTPError(401, "No login credentials")


# @cherrypy.expose()
# class Index(object):
#     # @cherrypy.expose()
#     @cherrypy.tools.json_in()
#     @cherrypy.tools.json_out()
#     def POST(self):
#         data = cherrypy.request.json
#         print(data, file=open("./python_log.txt", "a"))
#         sql_worker = Sqlite3Worker(auth_database_path)
#         response = authenticate(data)
#         sql_worker.close()
#         return response

#     def GET(self):
#         return "What are you even doing here?"


# if __name__ == "__main__":
#     conf = {
#         "/": {
#             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
#             "tools.sessions.on": True,
#             "tools.response_headers.on": True,
#             "tools.response_headers.headers": [
#                 ("Content-Type", "text/plain"),
#                 ("Access-Control-Allow-Origin", "http://localhost"),
#             ],
#         }
#     }

#     cherrypy.config.update(
#         {
#             "server.socket_host": "192.168.1.71",
#             "server.socket_port": 8081,
#             "tools.encode.on": True,
#             "tools.encode.encoding": "utf-8",
#             "request.show_tracebacks": False,
#             "request.process_request_body": True,
#         }
#     )

#     cherrypy.quickstart(Index(), "/", config=conf)

