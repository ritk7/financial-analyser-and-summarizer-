from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import json

# User class for authentication
class User(UserMixin):
    def __init__(self, id, name, username, email, password_hash):
        self.id = id
        self.name = name
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect('financial_analyzer.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, username, email, password_hash FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(*user_data)
        return None    
    
    @staticmethod
    def get_by_username(username):
        """Retrieve a user by username."""
        conn = sqlite3.connect('financial_analyzer.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, username, email, password_hash FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(*user_data)
        return None

    @classmethod
    def create_user(cls, name, username, email, password):
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect('financial_analyzer.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (name, username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return cls(user_id, name, username, email, password_hash)

# Transaction class
class Transaction:
    def __init__(self, id=None, user_id=None, date=None, description=None, 
                 amount=None, transaction_type=None, category=None, 
                 is_recurring=False, bank=None):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.description = description
        self.amount = amount
        self.transaction_type = transaction_type  # 'debit' or 'credit'
        self.category = category
        self.is_recurring = is_recurring
        self.bank = bank
    
    @staticmethod
    def save_transactions(transactions, user_id):
        conn = sqlite3.connect('financial_analyzer.db')
        cursor = conn.cursor()
        
        for transaction in transactions:
            # Convert date to string if it's a datetime object
            date_str = transaction.date
            if isinstance(transaction.date, datetime.datetime):
                date_str = transaction.date.strftime('%Y-%m-%d')
            
            cursor.execute(
                """
                INSERT INTO transactions 
                (user_id, date, description, amount, transaction_type, category, is_recurring, bank)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    date_str,
                    transaction.description,
                    transaction.amount,
                    transaction.transaction_type,
                    transaction.category,
                    transaction.is_recurring,
                    transaction.bank
                )
            )
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_user_transactions(user_id, start_date=None, end_date=None):
        conn = sqlite3.connect('financial_analyzer.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]
        
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        transactions = []
        for row in rows:
            transaction = Transaction(
                id=row['id'],
                user_id=row['user_id'],
                date=row['date'],
                description=row['description'],
                amount=row['amount'],
                transaction_type=row['transaction_type'],
                category=row['category'],
                is_recurring=bool(row['is_recurring']),
                bank=row['bank']
            )
            transactions.append(transaction)
        
        return transactions
    
    @staticmethod
    def update_transaction_category(transaction_id, category):
        conn = sqlite3.connect('financial_analyzer.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transactions SET category = ? WHERE id = ?",
            (category, transaction_id)
        )
        conn.commit()
        conn.close()

# Initialize the database tables
def init_db():
    conn = sqlite3.connect('financial_analyzer.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        category TEXT,
        is_recurring INTEGER DEFAULT 0,
        bank TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def load_user(user_id):
    return User.get_by_id(int(user_id))