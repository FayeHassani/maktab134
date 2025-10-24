import psycopg2
import logging
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s | %(levelname)s: %(message)s",
)
db_logger = logging.getLogger("Database")

class PostgresConnection:
    def __enter__(self):
        try:
            db_logger.info("Connecting to database ...")
            self.con = psycopg2.connect(
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            self.cur = self.con.cursor()
            db_logger.info("Connection established successfully!")
            return self
        except Exception as e:
            db_logger.error(f"Error connecting to database: {e}")
            raise e

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cur:
            self.cur.close()
        if self.con:
            self.con.close()
        db_logger.info("Connection closed.")

    def create_tables(self):
        try:
            # USERS
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    wallet DECIMAL(10,2) DEFAULT 0.0
                )
            """)
            # BUSES
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS buses (
                    bus_id SERIAL PRIMARY KEY,
                    bus_name VARCHAR(100) NOT NULL,
                    bus_number VARCHAR(50) UNIQUE NOT NULL,
                    total_seats INTEGER NOT NULL,
                    price_per_seat DECIMAL(10,2) NOT NULL,
                    departure_time VARCHAR(50),
                    arrival_time VARCHAR(50),
                    route VARCHAR(200)
                )
            """)
            # SEATS
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS seats (
                    seat_id SERIAL PRIMARY KEY,
                    bus_id INTEGER REFERENCES buses(bus_id) ON DELETE CASCADE,
                    seat_number INTEGER NOT NULL,
                    is_booked BOOLEAN DEFAULT FALSE,
                    UNIQUE(bus_id, seat_number)
                )
            """)
            # TICKETS
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                    bus_id INTEGER REFERENCES buses(bus_id) ON DELETE CASCADE,
                    seat_id INTEGER REFERENCES seats(seat_id) ON DELETE CASCADE,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    price DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'PAID'
                )
            """)
            # TRANSACTIONS
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    type VARCHAR(20),
                    amount DECIMAL(10,2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # AUDIT LOG
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id SERIAL PRIMARY KEY,
                    actor_id INTEGER REFERENCES users(user_id),
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.con.commit()
            print("Tables created successfully.")

            # ایجاد ادمین پیش‌فرض
            self.cur.execute("SELECT * FROM users WHERE email = 'admin@admin.com'")
            if not self.cur.fetchone():
                self.cur.execute("""
                    INSERT INTO users (name, email, password, is_admin, wallet)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("Admin", "admin@admin.com", "admin123", True, 0))
                self.con.commit()
                print("Default admin created: admin@admin.com / admin123")
        except Exception as e:
            print(f"Error creating Tables: {e}")
            self.con.rollback()

    # --- Query Helpers ---
    def execute_query(self, query, params=None):
        try:
            if params:
                self.cur.execute(query, params)
            else:
                self.cur.execute(query)
            return True
        except Exception as e:
            db_logger.error(f"Error executing query: {e}")
            return False

    def fetch_one(self, query, params=None):
        try:
            if params:
                self.cur.execute(query, params)
            else:
                self.cur.execute(query)
            return self.cur.fetchone()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def fetch_all(self, query, params=None):
        try:
            if params:
                self.cur.execute(query, params)
            else:
                self.cur.execute(query)
            return self.cur.fetchall()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def commit(self):
        try:
            self.con.commit()
        except Exception as e:
            print(f"Error committing: {e}")

    def rollback(self):
        try:
            self.con.rollback()
        except Exception as e:
            print(f"Error rolling back: {e}")

    # --- Audit Log Helper ---
    def log_action(self, actor_id, action):
        self.execute_query(
            "INSERT INTO audit_log (actor_id, action) VALUES (%s, %s)",
            (actor_id, action)
        )
        self.commit()
