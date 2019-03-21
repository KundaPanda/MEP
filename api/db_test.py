#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2

try:
    conn = psycopg2.connect(
        database="tickets",
        user="postgres",
        password="kundapanda",
        host="localhost",
        port="5432",
    )

except Exception:
    print("I am unable to connect to the database")

table_name = "tickets"
cur = conn.cursor()
try:
    print("here")
    cur.execute(
        "select exists(select * from information_schema.tables where table_name=%s)"
        % table_name
    )
    print("here2")
    print(cur.rowcount)
    if cur.rowcount:
        print("here3")
        cur.execute("DROP TABLE '%s'" % table_name)
    print("here4")
    cur.execute(
        """CREATE TABLE "%s" (id serial PRIMARY KEY, code integer, used integer, time TIMESTAMP)"""
        % (table_name)
    )
except Exception as e:
    print(e)
    print("I can't drop our test database!")

conn.commit()  # <--- makes sure the change is shown in the database
conn.close()
cur.close()
