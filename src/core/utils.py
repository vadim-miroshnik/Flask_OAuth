"""Create superuser"""

import logging

from core.db import db
from core.settings import settings
from models.db_models import Permission, PermissionType, Role, User


def add_super_user():
    if not (super_user := User.query.filter_by(login="superuser").first()):
        logging.info("Создается пользователь 'superuser'")
        super_user = User(login=settings.superuser.username, plain_password=settings.superuser.password)
        db.session.add(super_user)
    if not (role := Role.query.filter_by(name="superuser").first()):
        raise Exception("Не существует роли 'superuser'")
    super_user.roles.append(role)
    db.session.commit()


def add_role_superuser():
    # Получаем или создаем роль суперпользователя
    if not (role := Role.query.filter_by(name="superuser").first()):
        logging.info("Создается роль 'superuser'")
        role = Role(name="superuser")
        db.session.add(role)
    for required_permission in PermissionType:
        db_permissions = [item.name for item in Permission.query.all()]
        if required_permission not in db_permissions:
            logging.info(f"Для роли superuser создается разрешение '{required_permission.name}'")
            role.permissions.append(Permission(name=required_permission))
    db.session.commit()
