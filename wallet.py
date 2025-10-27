# wallet.py
from datetime import datetime
from audit_log import AuditLogger

class WalletManager:
    def __init__(self, db):
        """
        db: نمونه‌ای از PostgresConnection یا مشابه که متدهای:
            execute_query, fetch_one, fetch_all, commit, rollback, cur وجود داشته باشند.
        """
        self.db = db
        self.audit = AuditLogger(db)
        self._ensure_tables()

    def _ensure_tables(self):
        """ایجاد جدول transactions در صورت نبودن"""
        query = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            amount NUMERIC(10,2) NOT NULL,
            transaction_type VARCHAR(20) NOT NULL, -- DEPOSIT, TICKET_PURCHASE, REFUND
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.db.execute_query(query)
        self.db.commit()

    def add_balance(self, user_id: int, amount: float, description: str = "Wallet deposit") -> bool:
        """افزایش موجودی کیف پول و ثبت تراکنش"""
        if amount <= 0:
            print("Amount must be positive.")
            return False

        try:
            self.db.cur.execute("BEGIN;")
            # آپدیت کیف پول
            if not self.db.execute_query(
                "UPDATE users SET wallet = wallet + %s WHERE user_id = %s;",
                (amount, user_id)
            ):
                self.db.cur.execute("ROLLBACK;")
                print("Failed to update wallet.")
                return False

            # ثبت تراکنش
            self.db.execute_query(
                "INSERT INTO transactions (user_id, amount, transaction_type, description) VALUES (%s, %s, %s, %s);",
                (user_id, amount, 'DEPOSIT', description)
            )

            self.db.commit()
            self.audit.log(user_id, f"Deposit: +{amount:.2f} ({description})")
            print(f"✅ Added ${amount:.2f} to user {user_id} wallet.")
            return True
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            print(f"Error in add_balance: {e}")
            return False

    def deduct_balance(self, user_id: int, amount: float, description: str = "Ticket purchase") -> bool:
        """
        کم کردن مبلغ (برای خرید بلیط).
        این تابع خودش از FOR UPDATE روی ردیف کاربر استفاده نمی‌کند
        چون معمولاً buy_ticket تراکنش و FOR UPDATE را انجام می‌دهد.
        اما اگر جداگانه استفاده شود، امن بودن تراکنش حتماً باید تضمین شود.
        """
        if amount <= 0:
            print("Invalid amount.")
            return False

        try:
            self.db.cur.execute("BEGIN;")
            row = self.db.fetch_one("SELECT wallet FROM users WHERE user_id = %s FOR UPDATE;", (user_id,))
            if not row:
                self.db.cur.execute("ROLLBACK;")
                print("User not found.")
                return False

            wallet_balance = float(row[0])
            if wallet_balance < amount:
                self.db.cur.execute("ROLLBACK;")
                print("Insufficient wallet balance.")
                return False

            # کم کردن موجودی
            if not self.db.execute_query("UPDATE users SET wallet = wallet - %s WHERE user_id = %s;", (amount, user_id)):
                self.db.cur.execute("ROLLBACK;")
                print("Failed to deduct wallet.")
                return False

            # ثبت تراکنش (ثبت مقدار مثبت یا منفی بستگی به سیاست شما دارد؛ اینجا مثبت ذخیره می‌کنیم و نوع را مشخص می‌کنیم)
            self.db.execute_query(
                "INSERT INTO transactions (user_id, amount, transaction_type, description) VALUES (%s, %s, %s, %s);",
                (user_id, -abs(amount), 'TICKET_PURCHASE', description)
            )

            self.db.commit()
            self.audit.log(user_id, f"Purchase: -{amount:.2f} ({description})")
            return True
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            print(f"Error in deduct_balance: {e}")
            return False

    def refund_balance(self, user_id: int, amount: float, description: str = "Ticket refund") -> bool:
        """بازگرداندن مبلغ به کیف پول (رفاند) و ثبت تراکنش"""
        if amount <= 0:
            print("Invalid refund amount.")
            return False

        try:
            self.db.cur.execute("BEGIN;")
            if not self.db.execute_query("UPDATE users SET wallet = wallet + %s WHERE user_id = %s;", (amount, user_id)):
                self.db.cur.execute("ROLLBACK;")
                print("Failed to update wallet for refund.")
                return False

            self.db.execute_query(
                "INSERT INTO transactions (user_id, amount, transaction_type, description) VALUES (%s, %s, %s, %s);",
                (user_id, amount, 'REFUND', description)
            )

            self.db.commit()
            self.audit.log(user_id, f"Refund: +{amount:.2f} ({description})")
            print(f"✅ Refunded ${amount:.2f} to user {user_id}.")
            return True
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            print(f"Error in refund_balance: {e}")
            return False

    def get_balance(self, user_id: int) -> float:
        """بازگشت موجودی فعلی کیف پول"""
        try:
            row = self.db.fetch_one("SELECT wallet FROM users WHERE user_id = %s;", (user_id,))
            return float(row[0]) if row and row[0] is not None else 0.0
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    def show_transactions(self, user_id: int, limit: int = 50):
        """نمایش تاریخچه تراکنش‌ها"""
        try:
            rows = self.db.fetch_all(
                "SELECT transaction_id, amount, transaction_type, description, created_at FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s;",
                (user_id, limit)
            )
            if not rows:
                print("No transactions found.")
                return

            print(f"\n📜 Transactions for user {user_id}:")
            print("-" * 80)
            for t_id, amount, t_type, desc, created in rows:
                print(f"[{created}] ({t_type}) {amount:.2f} — {desc} (id={t_id})")
            print("-" * 80)
        except Exception as e:
            print(f"Error showing transactions: {e}")
