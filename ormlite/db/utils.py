from ormlite.base import configuration


Min = lambda x:'MIN("%s")' % x

Max = lambda x:'MAX("%s")' % x

Sum = lambda x:'SUM("%s")' % x

Count = lambda x:'COUNT("%s")' % x

Avg = lambda x:'AVG("%s")' % x



def create_tables(models,db):
    Table = configuration.db_engine.table.Table
    connection = db.get_connector()
    for model in models:
        Table(model).create(connection)
    connection.commit()
    connection.close()
