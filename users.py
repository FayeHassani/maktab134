from db_connect import PostgresConnection, db_logger

class User:
    def __init__(self, user_id, name, email, password, wallet=0.0, is_admin=False):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password
        self.wallet = wallet
        self.is_admin = is_admin

    def __str__(self):
        return f"User(name={self.name}, email={self.email}, wallet=${self.wallet})"


class Customer(User):
    def __init__(self, user_id, name, email, password, wallet=0.0, is_admin=False):
        super().__init__(user_id, name, email, password, wallet)

    def __str__(self):
        return f"Customer(name={self.name}, email={self.email}, wallet=${self.wallet})"


class Admin(User):
    def __init__(self, user_id, name, email, password, wallet=0.0, is_admin=True):
        super().__init__(user_id, name, email, password, wallet, is_admin)

    def __str__(self):
        return f"Admin(name={self.name}, email={self.email})"


class UserManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    # Register user
    def register_user(self, name, email, password):
        try:
            # checking emial 
            query = "SELECT * FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))
            if result:
                db_logger.warning("Email already exists.")
                return False

            query = "INSERT INTO users (name, email, password, is_admin, wallet) VALUES (%s,%s,%s,%s,%s)"
            success = self.db.execute_query(query, (name, email, password, False, 0))
            self.db.commit()
            if success:
                db_logger.info(f"User {name} registered successfully!")
                return True
            return False
        except Exception:
            db_logger.exception("Faild while registring user")
            self.db.rollback()
            return False

    def login_user(self, email, password):
        try:
            query = "SELECT user_id, name, email, password, wallet, is_admin FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))
            if not result:
                db_logger.error("User not found")
                return None

            user_id, name, db_email, db_password, wallet, is_admin = result
            if db_password != password:
                db_logger.error("Wrong password")
                return None

            if is_admin:
                return Admin(user_id, name, db_email, db_password, wallet)
            else:
                return Customer(user_id, name, db_email, db_password, wallet)
        except Exception:
            db_logger.exception("Login failed")
            return None

    def delete_user(self, user_id):
        try:
            query = "DELETE FROM users WHERE user_id = %s AND is_admin = FALSE"
            success = self.db.execute_query(query, (user_id,))
            self.db.commit()
            db_logger.info("User successfully deleted")
            return success
        except Exception:
            db_logger.exception("Error deleting user")
            self.db.rollback()
            return False

    #Get users (admin only)
    def get_all_users(self):
        try:
            query = "SELECT user_id, name, email, wallet, is_admin FROM users WHERE is_admin=FALSE"
            results = self.db.fetch_all(query)
            users = []
            for row in results:
                user_id, name, email, wallet, is_admin = row
                users.append({
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "wallet": float(wallet)
                })
            return users
        except Exception:
            db_logger.exception(f"Error fetching users")
            return []
