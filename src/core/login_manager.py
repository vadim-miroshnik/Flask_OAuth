"""Login manager"""

from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

from models.db_models import User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


def authenticate(login, password):
    user = User.query.filter_by(login=login).first()
    hash = generate_password_hash(user.password)
    if user and check_password_hash(hash, password):
        return user


def identity(payload):
    user_id = payload["sub"].strip('"')
    return User.query.filter_by(id=user_id).first()
