# import sqlite3
# from dataclasses import dataclass
#
#
# @dataclass
# class Database:
#     path_to_db: str
#
#
# def set_config(path_to_db: str = None):
#     Database.path_to_db = path_to_db
#     check_db_exist()
#
#
# def connect():
#     return sqlite3.connect(Database.path_to_db)
#
#
# def execute(sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
#     if not parameters:
#         parameters = ()
#     conn = connect()
#     conn.set_trace_callback(logger)
#     c = conn.cursor()
#     c.execute(sql, parameters)
#
#     if commit:
#         conn.commit()
#     data = None
#     if fetchall:
#         data = c.fetchall()
#     if fetchone:
#         data = c.fetchone()
#     conn.close()
#     return data
#
#
# def check_db_exist():
#     """Существует ли БД"""
#     sql = "SELECT count(name) FROM sqlite_master " \
#           "WHERE type='table' AND name='users'"
#     if execute(sql, fetchone=True)[0] == 0:
#         init_db()
#
#
# def init_db():
#     """Инициализирует БД"""
#     sql = """
#                 CREATE TABLE users (
#                     id int NOT NULL,
#                     name varchar(255) NOT NULL,
#                     email varchar(255),
#                     PRIMARY KEY (id)
#                     );
#         """
#     execute(sql, commit=True)
#
#
# def format_args(sql, parameters: dict):
#     sql += " AND ".join([
#         f"{item} = ?" for item in parameters
#     ])
#     return sql, tuple(parameters.values())
#
#
# def add_user(id: int, name: str, email: str = None):
#     sql = """
#          INSERT INTO users(id, Name, email) VALUES(?, ?, ?)
#          """
#     execute(sql, parameters=(id, name, email), commit=True)
#
#
# def select_all_users():
#     sql = """
#          SELECT * FROM users
#          """
#     return execute(sql, fetchall=True)
#
#
# def select_user(**kwargs):
#     # SQL_EXAMPLE = "SELECT * FROM Users where id=1 AND Name='John'"
#     sql = "SELECT * FROM users WHERE "
#     sql, parameters = format_args(sql, kwargs)
#     return execute(sql, parameters=parameters, fetchone=True)
#
#
# def logger(statement):
#     pass
#     # print(f"""
#     # Executing:
#     # {statement}
#     # _________________
#     # """)
