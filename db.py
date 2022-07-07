import sqlite3
import datetime
from os import system

def check_db():
    _ = system("cls")
    _datetime = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    databaseFile = ("database.db")
    db = sqlite3.connect(databaseFile, check_same_thread=False)
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        print("----   Database was found   ----")
    except sqlite3.OperationalError:
        cursor.execute("CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, nickname TEXT, reg_date TEXT, ref_id INT, balance INT)")
        db.commit()
        print("----   Database was create   ---")
    print(f"-----   {_datetime}   -----")
    print(f"---------   Users: {len(get_all_users())}   --------\n")

#------------------------------

def get_now_date():
    date = datetime.date.today()
    return date

def add_user_to_db(user_id, nickname, ref_id, balance):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    if not (cursor.execute(f"SELECT user_id FROM users WHERE user_id = '{user_id}'").fetchone()):
        cursor.execute(f"INSERT INTO users(user_id, nickname, reg_date, ref_id, balance) VALUES ({user_id}, '{nickname}', '{get_now_date()}', {ref_id}, {balance})")
    db.commit()

def get_users_exist(user_id):
    db = sqlite3.connect("database.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute(f"SELECT user_id FROM users WHERE user_id = '{user_id}'")
    if cursor.fetchone() is None:
        return False
    else:
        return True

def get_info(user_id):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
    row = cursor.fetchone()
    return row

def get_balance(user_id):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT balance FROM users WHERE user_id = {user_id}")
    row = cursor.fetchone()
    return row[0]

def set_balance(user_id, balance):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"UPDATE users SET balance = {balance} WHERE user_id IS {user_id}")
    db.commit()

def get_refs(user_id):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT user_id FROM users WHERE ref_id = {user_id}")
    row = cursor.fetchall()
    return len(row)

def get_all_users():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT user_id FROM users")
    row = cursor.fetchall()
    return row

def get_week_users():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute(f"""SELECT user_id FROM users WHERE ([reg_date] BETWEEN date('now', '-7 day') AND date('now'))""")
    row = cursor.fetchall()
    return row