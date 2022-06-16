import time
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, g

import auth
import database

bp = Blueprint('chats', __name__)


# Страница создания новой беседы
@bp.route('/add', methods=('GET', 'POST'))
@auth.login_required
def add():
    # Если была заполнена форма
    if request.method == 'POST':
        # Получаем имя из формы
        companion = request.form['username']
        if companion == g.user:
            flash("Нельзя создать чат с самим собой")
            return render_template('chats/add.html')
        # Проверяем существование такого пользователя
        db = database.get()
        user = db.execute(
            'SELECT * FROM logins WHERE username = ?', (companion,)
        ).fetchone()

        if user is None:
            flash("Такого пользователя не существует")
            return render_template('chats/add.html')
        # Проверяем наличие беседы
        existing_chat = db.execute(
            "SELECT * FROM chats WHERE companion = ? AND user = ?",
            (companion, g.user)
        ).fetchone()
        if existing_chat is not None:
            flash("Такая беседа уже есть")
            return render_template('chats/add.html')

        # Создаём беседу
        db.execute(
            """INSERT INTO chats (user, companion, last_msg_time, unread) 
            VALUES (:user, :comp, :time, FALSE),
            (:comp, :user, :time, TRUE)
            """,
            {'user': g.user, 'comp': companion, 'time': int(time.time())}
        )
        db.commit()
        return redirect(url_for('chats.chat', companion=companion))

    return render_template('chats/add.html')


# Страница чаты
@bp.route('/chat/<companion>', methods=('GET', 'POST'))
@auth.login_required
def chat(companion):
    db = database.get()
    timestamp_now = int(time.time())
    # Проверка есть ли такой чат
    existing_chat = db.execute(
        "SELECT * FROM chats WHERE user = ? AND companion = ?",
        (g.user, companion)
    ).fetchone()
    if existing_chat is None:
        flash(f"Чата с {companion} не существует, добавьте его сначала")
        return redirect(url_for('chats.home'))
    # Если была заполнена форма = отправлено сообщение
    if request.method == 'POST':
        # Получаем текст
        text = request.form['msg']
        if len(text) == 0:
            flash("Нельзя отправлять пустой текст")
        else:
            # Заносим сообщение
            db.execute("INSERT INTO messages (author, recipient, text, time, unread) VALUES (?, ?, ?, ?, TRUE)",
                       (g.user, companion, request.form['msg'], timestamp_now))
            # обновляем статусы чатов
            db.execute("UPDATE chats SET last_msg_time = ?, unread = TRUE WHERE user = ? AND companion = ?",
                       (timestamp_now, companion, g.user))
            db.execute("UPDATE chats SET last_msg_time = ? WHERE user = ? AND companion = ?",
                       (timestamp_now, g.user, companion))
            db.commit()
        return redirect(url_for("chats.chat", companion=companion))
    # Если просто была загружена страница
    # Загружаем последние 10 сообщений TODO добавить прокрутку
    messages = db.execute("""SELECT * FROM (SELECT * FROM messages 
                             WHERE (author = :user AND recipient = :comp) 
                             OR (author = :comp AND recipient = :user)
                             ORDER BY time DESC LIMIT 0, :count) ORDER BY time ASC """,
                          {"user": g.user, "comp": companion, "count": 10}).fetchall()
    # Сброс непрочитанности
    db.execute("UPDATE chats SET unread = FALSE WHERE user = ? AND companion = ?", (g.user, companion))
    db.execute("UPDATE messages SET unread = FALSE WHERE author = ? AND recipient = ?", (companion, g.user))
    db.commit()

    return render_template("chats/chat.html", companion=companion, messages=messages)


@bp.route('/home')
@auth.login_required
def home():
    # Запрашиваем все чаты
    db = database.get()
    chats = db.execute("SELECT * FROM chats WHERE user = ? ORDER BY last_msg_time DESC", (g.user,)).fetchall()

    # TODO Сделать норм структуру SQL вместо того чтобы в питоновском коде это делать
    chats_list = []
    for c in chats:
        chat_dict = {}
        chat_dict['companion'] = c['companion']
        chat_dict['unread'] = c['unread']
        last_time = datetime.fromtimestamp(c['last_msg_time'])
        # Показывать время если сообщение сегодняшнее, вместе с датой если нет
        if last_time.date() == datetime.now().date():
            chat_dict['time'] = last_time.strftime("%H:%M:%S")
        else:
            chat_dict['time'] = last_time.strftime("%m.%d %H:%M:%S")
        # Запрашиваем последнее сообщение (смотри туду выше)
        last_message = db.execute("""SELECT * FROM messages 
                                 WHERE (author = :user AND recipient = :comp) 
                                 OR (author = :comp AND recipient = :user)
                                 ORDER BY time DESC """,
                                  {"user": g.user, "comp": c['companion']}).fetchone()

        if last_message is not None:
            chat_dict['message'] = last_message['text']
            chat_dict['author'] = last_message['author']

        chats_list.append(chat_dict)
    return render_template('chats/home.html', chats=chats_list)
