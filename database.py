import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


# Подключение к базе данных
def get():
    if 'db' not in g:
        g.db = sqlite3.connect("db/chat.db")
        g.db.row_factory = sqlite3.Row

    return g.db


# Закрытие базы данных
def close(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# Создание базы данных
@click.command('init-db')
@with_appcontext
def init_db_command():
    db = get()
    with current_app.open_resource('db/init.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Initialized the database.')
