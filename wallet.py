from audit_log import AuditLogger
from db_connect import db_logger

class WalletManager:
    def __init__(self, db):
        self.db = db
        self.audit = AuditLogger(db)

    def add_balance(self, user_id: int, amount: float, type: str = "Wallet deposit") -> bool:
        if amount <= 0:
            db_logger.error("Amount must be positive.")
            return False

        try:
            # update wallet
            if not self.db.execute_query(
                "UPDATE users SET wallet = wallet + %s WHERE user_id = %s;",
                (amount, user_id)
            ):
                self.db.rollback()
                db_logger.error("Failed to update wallet.")
                return False

            # insert transaction
            self.db.execute_query(
                "INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s);",
                (user_id, type, amount)
            )

            self.db.commit()
            self.audit.log(user_id, f"Deposit: +{amount:.2f} ({type})")
            db_logger.info(f"Added ${amount:.2f} to user {user_id} wallet.")
            return True
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass
            db_logger.exception(f"Error adding balance for user {user_id}")
            return False

    def deduct_balance(self, user_id: int, amount: float, type: str = "Ticket purchase") -> bool:
        if amount <= 0:
            db_logger.error("Invalid amount.")
            return False

        try:
            # Lock wallet
            row = self.db.fetch_one("SELECT wallet FROM users WHERE user_id = %s FOR UPDATE;", (user_id,))
            if not row:
                db_logger.error("User not found")
                return False

            wallet_balance = float(row[0])
            if wallet_balance < amount:
                db_logger.error("Insufficient wallet balance.")
                return False

            # deduct balance
            if not self.db.execute_query("UPDATE users SET wallet = wallet - %s WHERE user_id = %s;", (amount, user_id)):
                db_logger.error("Failed to deduct wallet.")
                return False

            # transaction log
            self.db.execute_query(
                "INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s);",
                (user_id, type, -abs(amount))
            )

            self.audit.log(user_id, f"Purchase: -{amount:.2f} ({type})")
            db_logger.info(f"Deducted ${amount:.2f} from user {user_id} wallet.")
            return True
        except Exception:
            db_logger.exception(f"Error deducting balance for user {user_id}")
            return False

    def refund_balance(self, user_id: int, amount: float, type: str = "Ticket refund") -> bool:
        if amount <= 0:
            db_logger.error("Invalid refund amount.")
            return False

        try:
            # refund
            if not self.db.execute_query("UPDATE users SET wallet = wallet + %s WHERE user_id = %s;", (amount, user_id)):
                db_logger.error("Failed to update wallet for refund.")
                return False
            
            #log into trasnaction
            self.db.execute_query(
                "INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s);",
                (user_id, type, amount)
            )

            self.audit.log(user_id, f"Refund: +{amount:.2f} ({type})")
            db_logger.info(f"Refunded ${amount:.2f} to user {user_id}.")
            return True
        except Exception:
            db_logger.exception(f"Error refunding balance for user {user_id}")
            return False

    def get_balance(self, user_id: int) -> float:
        """بازگشت موجودی فعلی کیف پول"""
        try:
            row = self.db.fetch_one("SELECT wallet FROM users WHERE user_id = %s;", (user_id,))
            return float(row[0]) if row and row[0] is not None else 0.0
        except Exception:
            db_logger.exception(f"Error fetching balance for user {user_id}")
            return 0.0

    def show_transactions(self, user_id: int, limit: int = 50):
        try:
            rows = self.db.fetch_all(
                "SELECT transaction_id, type, amount, timestamp FROM transactions "
                "WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s;",
                (user_id, limit)
            )

            if not rows:
                db_logger.info(f"No transactions found for user {user_id}.")
                return []

            db_logger.info(f"Transactions for user {user_id}:")
            transactions = []
            for t_id, t_type, amount, created in rows:
                db_logger.info(f"[{created}] ({t_type}) {amount:.2f} (id={t_id})")
                transactions.append({
                    "transaction_id": t_id,
                    "type": t_type,
                    "amount": float(amount),
                    "timestamp": created
                })

            return transactions

        except Exception:
            db_logger.exception(f"Error showing transactions for user {user_id}")
            return []
