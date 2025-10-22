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


class UserManager:
    def __init__(self, db):
        self.db = db

    def register_user(self, name, email, password):
        try:
            query = "SELECT * FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))
            if result:
                print("Email already exists!")
                return False

            query = "INSERT INTO users (name, email, password, is_admin, wallet) VALUES (%s, %s, %s, %s, %s)"
            success = self.db.execute_query(query, (name, email, password, False, 0.0))
            if success:
                self.db.commit()
                print(f"User {name} registered successfully!")
                return True
            else:
                print("Failed! Try again!")
                return False
        except Exception as e:
            print(f"Registering user failed: {e}")
            return False

    def login_user(self, email, password):
        try:
            query = "SELECT user_id, name, email, password, wallet, is_admin FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))
            if not result:
                print("User not found!")
                return None

            user_id, name, db_email, db_password, wallet, is_admin = result
            if db_password != password:
                print("Wrong password! Please try again!")
                return None
            else:
                if is_admin:
                    return Admin(user_id, name, db_email, db_password, wallet)
                else:
                    return Customer(user_id, name, db_email, db_password, wallet)
        except Exception as e:
            print(f"Login failed: {e}")
            return None

    def delete_user(self, user_id):
        try:
            query = "DELETE FROM users WHERE user_id = %s AND is_admin = FALSE"
            success = self.db.execute_query(query, (user_id,))
            if success:
                self.db.commit()
                print("User deleted successfully!")
                return True
            else:
                print("Failed to delete user!")
                return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def update_wallet(self, user_id, amount):
        try:
            query = "UPDATE users SET wallet = wallet + %s WHERE user_id = %s"
            success = self.db.execute_query(query, (amount, user_id))
            if success:
                self.db.commit()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error updating wallet: {e}")
            return False

    def get_wallet(self, user_id):
        try:
            query = "SELECT wallet FROM users WHERE user_id = %s"
            result = self.db.fetch_one(query, (user_id,))
            return float(result[0]) if result else 0.0
        except Exception as e:
            print(f"Error getting wallet: {e}")
            return 0.0

    def get_all_users(self):
        try:
            query = "SELECT user_id, name, email, wallet, is_admin FROM users WHERE is_admin = FALSE"
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
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
