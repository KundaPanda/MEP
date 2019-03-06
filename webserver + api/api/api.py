#!C:/Users/vojdo/AppData/Local/Programs/Python/Python37/python.exe

import db_handler
import sqlite3
from sqlite3worker import Sqlite3Worker
import json
import sys
import hashlib
import cherrypy
from time import time

auth_database_path = "../databases/auth.db"
sql_worker = Sqlite3Worker(auth_database_path)

auth_table_name = "auth"


def authenticated(commands):
    response = cherrypy.response
    response.status = '200 OK'
    result = db_handler.get_commands(commands)
    return result


def removekey(d, key):
    r = dict(d)
    del r[key]
    return r


def authenticate(data):
    if ("username" in data and "password" in data):
        username = data["username"]
        password = data["password"]
        password = hashlib.sha3_256(password.encode('UTF-8')).hexdigest()

        countt = sql_worker.execute(
            'SELECT COUNT(password) FROM {} WHERE username="{}" AND password="{}"'
            .format(auth_table_name, username, password))
        countt = countt[0][0]
        if countt == 1:

            commands = removekey(data, "username")
            del commands["password"]

            result = authenticated(commands)

            return result
        else:
            raise cherrypy.HTTPError(401, "Bad login credentials")
    else:
        raise cherrypy.HTTPError(401, "No login credentials")


@cherrypy.expose()
class Index(object):
    # @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        data = cherrypy.request.json
        print(data, file=open("./python_log.txt", "a"))
        sql_worker = Sqlite3Worker(auth_database_path)
        response = authenticate(data)
        sql_worker.close()
        return response

    def GET(self):
        return "What are you even doing here?"


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch':
            cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on':
            True,
            'tools.response_headers.on':
            True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain'),
                                               ('Access-Control-Allow-Origin',
                                                'http://localhost')],
        }
    }

    cherrypy.config.update({
        'server.socket_host': '192.168.1.71',
        'server.socket_port': 8081,
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'request.show_tracebacks': False,
        'request.process_request_body': True
    })

    cherrypy.quickstart(Index(), '/', config=conf)