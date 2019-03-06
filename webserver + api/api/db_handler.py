#!C:/Users/vojdo/AppData/Local/Programs/Python/Python37/python.exe

import sqlite3
from sqlite3worker import Sqlite3Worker
import cgitb
import json
import sys, inspect
import hashlib
import copy
from time import time


class ticket:
    def __init__(t, ID, num, countt, used, time, valid):
        t.ID = int(ID)
        t.num = str(num)
        t.countt = countt
        t.used = int(used)
        t.time = int(time)
        t.valid = bool(valid)


database_path = "../databases/ticketr.db"
table_name = "ticket"
table_headers = ["ID", "num", "used", "time", "countt", "valid"]

sql_worker = Sqlite3Worker(database_path)


def get_with_headers(alist):
    result = {}
    for index in range(len(alist)):
        result[table_headers[index]] = alist[index]
    return result


def update(table_name, tick):
    print("UPDATE", file=open("./python_log.txt", "a"))
    tick.used = 1
    tick.time = int(round(time() * 1000))
    tick.countt += 1
    tick.valid = 0
    sql_worker.execute(
        "UPDATE {} SET used={}, time={}, countt={}, valid={} WHERE num='{}'".
        format(table_name, tick.used, tick.time, tick.countt, tick.valid,
               tick.num))
    return tick


def get_all(table_name, tick):
    result = sql_worker.execute('SELECT * FROM {}'.format(table_name))
    results = []
    for res in result:
        results.append(get_with_headers(res))
    return results


def get_one(table_name, tick):
    try:
        len(tick.__dict__["num"]) > 0
        sql_worker_internal = Sqlite3Worker(database_path)
        result = sql_worker_internal.execute(
            'SELECT * FROM {} WHERE num="{}"'.format(table_name, tick.num))
        try:
            result = get_with_headers(result[0])
        except IndexError:
            return {}
        sql_worker_internal.close()
        print(result, file=open("./python_log.txt", "a"))
        return result
    except AttributeError:
        return {}


def update_one(table_name, tick):
    try:
        print(tick.__dict__, file=open("./python_log.txt", "a"))
        tick = get_ticket_attributes(table_name, tick)
        if tick.ID == 0:
            return {}
        num = tick.num
        used = sql_worker.execute('SELECT used FROM {} WHERE num="{}"'.format(
            table_name, num))
        if used:
            used = (used[0][0])
            if used == 0:
                tick.valid = 1
            else:
                tick.valid = 0
            return_tick = copy.deepcopy(tick)
            update(table_name, tick)
        else:
            tick.count = -1
        print(return_tick, file=open("./python_log.txt", "a"))
        return return_tick.__dict__
    except AttributeError:
        return {}


def get_ticket_attributes(table_name, tick):
    result = get_one(table_name, tick)
    if result != {}:
        tick.ID = result["ID"]
        tick.num = result["num"]
        tick.countt = result["countt"]
        tick.used = result["used"]
        tick.time = result["time"]
        tick.valid = result["valid"]
    return tick


def get_commands(commands):
    tic = []
    if len(commands) == 2:
        tic = commands["ticket"]
        comm = commands["command"]
    else:
        comm = commands["command"]
    if len(tic) > 0:
        tick = {
            "ID": 0,
            "num": "",
            "countt": 0,
            "used": 0,
            "time": 0,
            "valid": 0
        }
        print(tic, type(tic), file=open("./python_log.txt", "a"))
        if (isinstance(tic, str)):
            tic = json.loads(tic)
        tic = tic[0]
        print(tic, type(tic), file=open("./python_log.txt", "a"))

        if (isinstance(tic, str)):
            tic = json.loads(tic)

        for key, value in tic.items():
            tick[key] = value
        comm = commands["command"]
        tick = ticket(tick["ID"], tick["num"], tick["countt"], tick["used"],
                      tick["time"], tick["valid"])
        print(tick, file=open("./python_log.txt", "a"))
        print(tick.__dict__, file=open("./python_log.txt", "a"))
    else:
        tick = tic[:]

    members = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    memdict = {}
    for member in members:
        memdict[member[0]] = member[1]

    sql_worker = Sqlite3Worker(database_path)

    try:
        result = memdict[comm](table_name, tick)
    except TypeError:
        result = {}

    sql_worker.close()

    return result
