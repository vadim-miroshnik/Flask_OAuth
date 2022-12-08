from app import app
from core.db import db
from core.utils import add_role_superuser, add_super_user

db.init_app(app)

with app.app_context():
    db.create_all()
    db.session.commit()
    add_role_superuser()
    add_super_user()

