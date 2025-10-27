from db_connect import PostgresConnection

with PostgresConnection() as db:
    db.create_tables()
