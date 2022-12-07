import sqlite3
from flask import g


def connect_db(db):
    """Соединяет с указанной базой данных."""
    print("connect db !!!!!")
    rv = sqlite3.connect(db)  # внутри конфигураций надо будет указать БД, в которую мы будем все хранить
    rv.row_factory = sqlite3.Row  # инстанс для итерации по строчкам (может брать по строке и выдавать)
    return rv


def get_db(db):
    """Если ещё нет соединения с базой данных, открыть новое - для текущего контекста приложения"""
    print("get db !!!!!")
    if not hasattr(g, 'sqlite_db'):  # g - это наша глобальная переменная, являющасяс объектом отрисовки
        g.sqlite_db = connect_db(db)
    return g.sqlite_db


def init_db(app, db):
    """Инициализируем наше БД"""
    print("init db !!!!!")
    with app.app_context(), app.open_resource('schema.sql', mode='r') as f:  # внутри app_context app и g связаны
        db = get_db(db)
        try:
            db.cursor().executescript(f.read())
        except:
            pass
        db.commit()
