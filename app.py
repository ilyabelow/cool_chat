from flask import Flask
import secrets

import auth
import chats
import database


app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)
app.teardown_appcontext(database.close)
app.cli.add_command(database.init_db_command)

app.register_blueprint(auth.bp)
app.register_blueprint(chats.bp)


if __name__ == '__main__':
    app.run()
