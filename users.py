from db_connect import PostgresConnection

class User:
    def __init__(self, user_id, name, email, password, wallet = 0.0):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password
        self.wallet = wallet

        def __str__(self):
            return f" User name : {self.name}, User email : {self.email}"
        

class UserManager:
    def __init__(self, db):
        self.db = db
    
    def register_user(self, name, email, password):
        try:
            #Check email if exists
            query = "SELECT * FROM users WHERE email = %s"
            result = self.db.fetxh_one(query, (email,))

            if result: 
                print("Email already exists!")
                return False
        
            #Insert new user
            query = "INSERT INTO users (name, email, password, is_admin, wallet) VALUES (%s, %s, %s, %s, %s)"
            success = self.db.execute_query(query, (name, email, password, False, 0,0))
            
            if success:
                print(f"User {name} registered successfully!")
                return True
            else:
                print("Faild! Try again!")
                return False
        
        except Exception as e:
            print(f" Rgistering user was Faild! :{e}")
            return False
        
    def login_user(self, email, password):
        try:
            query = "SELECT user_id, name, email, password, wallet, is_admin FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))

            if not result:
                print("User NOT found!")
                return None
            
            user_id, name, db_email, db_password, wallet, is_admin = result

            if db_password != password:
                print("wrong password! Please try again!")
                return None
            else:
                print(f"Welcome {name}! I hope have a good experience with us!")
                return User(user_id, name, db_email, db_password, wallet)
        except Exception as e:
            print("logging in was Faild! Try agian later!")
            return None
        
    def delete_user(self, user_id):
        try:
            query = "DELETE FROM user WHERE user_id = %s AND is_admin = FALSE"
            success = self.db.execute_query(query, (user_id,))

            if success:
                print("User deleted successfully!")
                return True
            else:
                print("Faild to delete user!")
                return False
        
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
        
    def update_wallet(self, user_id, amount):
        try:
            query = "UPDATE users SET wallet = wallet + %s WHERE user_id = %s"
            success = self.db.execute_query(query, (amount, user_id))

            if success:
                return True
            else:
                return False

        except Exception as e:
            print(f"Error updating wallet:{e}")
            return False

    def get_wallet(self, user_id):
        try:
            query = "SELECT wallet FROM users WHERE user_id = %s"
            result = self.db.fetch_one(query,(user_id,))

            if result:
                return result[0]
            else:
                return 0.0

        except Exception as e:
            print(f"Error getting wallet: {e}")
            return 0
        

class Customer(User):
    def __init (self, user_id, name, email, password, wallet = 0.0):
        super().__init__(user_id, name, email, password, wallet)
        
    def __str__(self):
        return f"Customer(name:{self.name}, email:{self.email}, wallet: ${self.wallet})"
    



class Admin(User):
    def __init__(self, user_id, name, email, password, wallet=0.0):
        super().__init__(user_id, name, email, password, wallet)
    
    def __str__(self):
        return f"Admin(name={self.name}, email={self.email})"
