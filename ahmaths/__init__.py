from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from ahmaths.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validate critical configuration
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in environment variables or config.json")
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise ValueError("SQLALCHEMY_DATABASE_URI (or DATABASE_URL) must be set in environment variables or config.json")

    app.url_map.strict_slashes = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    from ahmaths.users.routes import users
    from ahmaths.main.routes import main
    from ahmaths.questions.routes import questions
    from ahmaths.papers.routes import papers
    from ahmaths.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(questions)
    app.register_blueprint(papers)
    app.register_blueprint(errors)

    return app
