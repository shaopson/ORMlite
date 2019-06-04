import sqlite3
from ormlite.fields import Mappings

def create_table(models,db):
	sql_create = []
	for model in models:
		table = model.__table__
		definitions = []
		for name,field in model.__mapping__.items():
			column = Mappings.get_column(field)
			definition = "%s %s %s" % (name,column,field.constraint())
			definitions.append(definition)
		for name,field in model.__relation__.items():
			definitions.append(field.joint(name))
		sql = "CREATE TABLE %s (%s);" % (table,','.join(definitions))
		print(sql)
		sql_create.append(sql)
	with sqlite3.connect(db) as conn:
		cur = conn.cursor()
		for sql in sql_create:
			cur.execute(sql)
		cur.close()
		conn.commit()


