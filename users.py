from db_connect import PostgresConnection

class User:
    def __init__(self, user_id, name, email, password, wallet=0.0, is_admin=False):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password
        self.wallet = wallet
        self.is_admin = is_admin

    def __str__(self):
        return f"User(name: {self.name}, email: {self.email}, wallet: ${self.wallet})"


class Customer(User):
    def __init__(self, user_id, name, email, password, wallet=0.0):
        super().__init__(user_id, name, email, password, wallet, is_admin=False)

    def __str__(self):
        return f"Customer(name: {self.name}, email: {self.email}, wallet: ${self.wallet})"


class Admin(User):
    def __init__(self, user_id, name, email, password, wallet=0.0):
        super().__init__(user_id, name, email, password, wallet, is_admin=True)

    def __str__(self):
        return f"Admin(name: {self.name}, email: {self.email})"

from db_connect import PostgresConnection
from main import Customer, Admin, User

class UserManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    def register_user(self, name, email, password):
        result = self.db.fetch_one("SELECT * FROM users WHERE email=%s;", (email,))
        if result:
            print("Email already exists!")
            return False
        self.db.execute_query("INSERT INTO users (name,email,password,is_admin,wallet) VALUES (%s,%s,%s,%s,%s);",
                              (name, email, password, False, 0))
        # ثبت لاگ
        user = self.db.fetch_one("SELECT user_id FROM users WHERE email=%s;", (email,))
        if user:
            self.db.log_action(user[0], f"Registered new user {email}")
        self.db.commit()
        print(f"User {name} registered successfully!")
        return True

    def login_user(self, email, password):
        result = self.db.fetch_one("SELECT user_id,name,email,password,wallet,is_admin FROM users WHERE email=%s;", (email,))
        if not result:
            print("User NOT found!")
            return None
        user_id, name, db_email, db_password, wallet, is_admin = result
        if db_password != password:
            print("Wrong password!")
            return None
        if is_admin:
            return Admin(user_id, name, db_email, db_password, wallet)
        else:
            return Customer(user_id, name, db_email, db_password, wallet)

    def update_wallet(self, user_id, amount):
        self.db.execute_query("UPDATE users SET wallet = wallet + %s WHERE user_id=%s;", (amount, user_id))
        self.db.execute_query("INSERT INTO transactions (user_id,type,amount) VALUES (%s,%s,%s);",
                              (user_id, "WALLET_TOPUP", amount))
        self.db.log_action(user_id, f"Wallet topped up by {amount}")
        self.db.commit()
        return True

