import sqlite3
import datetime as dt

conn = sqlite3.connect(":memory:")
conn.execute("""
	CREATE TABLE test (name VARChar(50),dt DATETIME);
	""")
conn.execute("INSERT INTO test (name,dt) VALUES (?,?)",['name',dt.datetime.today()])
conn.execute("INSERT INTO test (name,dt) VALUES (?,?)",['shao',dt.datetime.today()])
conn.execute("INSERT INTO test (name,dt) VALUES (?,?)",['wen',dt.datetime.today()])
conn.execute("INSERT INTO test (name,dt) VALUES (?,?)",['ling',dt.datetime.today()])
result = conn.execute("select * from test where dt > '2019-01-01' ;")
print(result.fetchall())

