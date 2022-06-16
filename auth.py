import functools
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, g
from werkzeug.security import check_password_hash, generate_password_hash

import database

bp = Blueprint('auth', __name__)


# Регистрация
@bp.route('/register', methods=('GET', 'POST'))
def register():
    # Если форма заполнена
    if request.method == 'POST':
        # Получаем поля формы
        username = request.form['username']
        password = request.form['password']
        db = database.get()
        # Проверка корректности ввода (на всякий случай)
        if not username:
            flash("Не введено имя")
        elif not password:
            flash("Не введён пароль")
        else:
            # Проверка доступности имени
            user = db.execute(
                'SELECT * FROM logins WHERE username = ?', (username,)
            ).fetchone()
            if user is not None:
                flash(f"Имя {username} уже занято")
            else:
                # ДОбавление пользователя
                db.execute(
                    "INSERT INTO logins (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                # Сразу входим
                set_logged_in(username)
                return redirect(url_for("chats.home"))

    return render_template('auth/register.html')


# Вход
@bp.route('/login', methods=('GET', 'POST'))
def login():
    # Если форма была заполнена
    if request.method == 'POST':
        # Получение данных формы
        username = request.form['username']
        password = request.form['password']
        db = database.get()
        user = db.execute(
            'SELECT * FROM logins WHERE username = ?', (username,)
        ).fetchone()
        # Проверка введённых данных
        if user is None:
            flash('Неверное имя пользователя')
        elif not check_password_hash(user['password'], password):
            flash('Неверный пароль')
        else:
            # Успех
            set_logged_in(username)
            return redirect(url_for('chats.home'))
    # Если форма не была введена
    return render_template('auth/login.html')


# Установка куки что пользователь авторизован
def set_logged_in(username):
    session.clear()
    session['user'] = username


@bp.before_app_request
def load_logged_in_user():
    g.user = session.get('user')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))


# Редирект на главную авторизации если пользователь не вошёл
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.index'))
        return view(**kwargs)

    return wrapped_view


# Редирект на домашнюю страницу если пользователь вошёл
def only_when_not_logged_in(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is not None:
            return redirect(url_for('chats.home'))
        return view(**kwargs)

    return wrapped_view


# Гравная (авторизации)
@bp.route('/')
@only_when_not_logged_in
def index():
    return render_template('auth/index.html')
