"""User endpoints"""

import logging
import uuid
from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint, request, jsonify, abort
from flask_jwt import jwt_required
from sqlalchemy import exc

from api.route.static import swagger_param_auth_token
from core.db import db
from models.db_models import User, Role
from api.route.decorators import user_has, user_is
from api.route.error_messages import ErrMsgEnum


api_admin_user = Blueprint("admin_user", __name__)


@api_admin_user.route("<string:id>/role/", methods=["PUT"])
@swag_from(
    {
        "description": "Update roles for user",
        "tags": ["admin user"],
        "parameters": [
            {
                "description": "uuid user",
                "in": "path",
                "name": "id",
                "required": "true",
                "schema": {"type": "string", "format": "uuid"},
            },
            {
                "description": "applying to user list of roles identified by uuid",
                "in": "body",
                "name": "body",
                "required": "true",
                "schema": {
                    "id": "UUID_list",
                    "type": "array",
                    "items": {"schema": {"id": "id", "type": "string", "format": "uuid"}},
                },
            },
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Update roles for user",
            },
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
            int(HTTPStatus.UNAUTHORIZED): {"description": "Unauthorized", "schema": {"type": "string"}},
            int(HTTPStatus.FORBIDDEN): {"description": "Forbidden", "schema": {"type": "string"}},
        },
    }
)
@jwt_required()
@user_has("all_write")
def user_role_update(id):
    try:
        uuid.UUID(id)
        user = User.query.filter_by(id=id).one()
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.FORMAT_ERROR)
    except exc.NoResultFound:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.MISSING_USER)
    logging.debug("%s", user)
    user.roles = []
    try:
        for role_id in request.json:
            logging.debug("%s", role_id)
            uuid.UUID(role_id)
            role = Role.query.filter_by(id=role_id).one()
            logging.debug("%s", role)
            user.roles.append(role)
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.FORMAT_ERROR)
    except exc.NoResultFound:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.MISSING_ROLE)
    db.session.commit()
    return jsonify(dict(status="success")), HTTPStatus.CREATED
