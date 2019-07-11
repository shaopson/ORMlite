import sqlite3
import datetime as dt

conn = sqlite3.connect(":memory:")
conn.execute("""
	CREATE TABLE test (name VARChar(50),dt DATETIME,age INT);
	""")
conn.execute("INSERT INTO test (name,dt,age) VALUES (?,?,?)",['name',dt.datetime.today(),1])
conn.execute("INSERT INTO test (name,dt,age) VALUES (?,?,?)",['shao',dt.datetime.today(),2])
conn.execute("INSERT INTO test (name,dt,age) VALUES (?,?,?)",['wen',dt.datetime.today(),4])
conn.execute("INSERT INTO test (name,dt,age) VALUES (?,?,?)",['ling',dt.datetime.today(),4])
result = conn.execute("select * from test where dt > '2019-01-01 12:00:00' ;")
l = result.fetchall()
print(l)
print(isinstance(l[0][2],int))

