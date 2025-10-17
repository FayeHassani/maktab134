from db_connect import PostgresConnection




with PostgresConnection() as db:
    db.execute(create_table_query)
    db.commit()
    print("✅ Table 'users' created successfully!")


 