from ormlite.base import configuration


def create_tables(models,db):
    Table = configuration.db_engine.table.Table
    connection = db.get_connector()
    for model in models:
        Table(model).create(connection)
    connection.commit()
    connection.close()
