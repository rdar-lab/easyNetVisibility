import os
from flask import Flask, jsonify
from flask_mail import Mail
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect

import db
# Local Scripts
import email
import general_utils
import validators

csrf = CSRFProtect()

def create_app():
    global app
    """ Flask application factory """
    # Setup Flask app and app.config
    app = Flask(__name__)
    app.config.from_envvar('APP_CONFIG')
    app.config['SECRET_KEY'] = os.urandom(32)

    mail = Mail(app)
    recipient = app.config['MAIL_RECIPIENT']
    email.init(mail, recipient)

    db.init(app.config['DB_HOST'],
            app.config['DB_PORT'],
            app.config['DB_USER'],
            app.config['DB_PASSWORD'],
            app.config['DB_DATABASE'])

    csrf.init_app(app)


    @app.errorhandler(CSRFError)
    # @csrf.error_handler
    def csrf_error(reason):
        # noinspection PyBroadException
        try:
            return jsonify(reason=reason)
        except:
            return str(reason)

    return app


# This needs to be in the end of the file, due to loading order
app = create_app()
import ui
import api
