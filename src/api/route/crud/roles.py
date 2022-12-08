"""Roles endpoints"""

import logging
import uuid
from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint, request, jsonify, abort
from flask_jwt import jwt_required
from sqlalchemy import exc

from api.route.static import swagger_param_auth_token
from api.schema.role import RoleSchema, RoleSchemaInfo
from core.db import db
from models.db_models import Role, Permission
from api.route.decorators import user_has, user_is
from api.route.error_messages import ErrMsgEnum


api_admin_role = Blueprint("admin_role", __name__)


@api_admin_role.route("/")
@swag_from(
    {
        "tags": ["admin roles"],
        "parameters": [
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.OK): {
                "description": "Get roles",
                "schema": {
                    "id": "RolesList",
                    "type": "array",
                    "items": RoleSchemaInfo,
                },
            }
        },
    }
)
@jwt_required()
@user_has("all_read")
def get_roles():
    roles_data = RoleSchema(many=True).dump(Role.query.all())
    logging.debug("%s", roles_data)
    return roles_data, HTTPStatus.OK


@api_admin_role.route("/<string:id>")
@swag_from(
    {
        "tags": ["admin roles"],
        "parameters": [
            {"in": "path", "name": "id", "required": "true", "schema": {"type": "string"}},
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.OK): {"description": "Get roles", "schema": RoleSchema},
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
        },
    }
)
@jwt_required()
@user_has("all_read")
def get_role(id):
    role = Role.query.filter_by(id=id).one()
    logging.debug("%s", role.permissions)
    role_data = RoleSchema().dump(role)
    logging.debug("%s", role_data)
    return role_data, HTTPStatus.OK


@api_admin_role.route("/", methods=["POST"])
@swag_from(
    {
        "tags": ["admin roles"],
        "parameters": [
            {"in": "path", "name": "name", "required": "true", "type": "string"},
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Create role",
            },
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
            int(HTTPStatus.UNAUTHORIZED): {"description": "Unauthorized", "schema": {"type": "string"}},
            int(HTTPStatus.FORBIDDEN): {"description": "Forbidden", "schema": {"type": "string"}},
        },
    }
)
@jwt_required()
@user_has("all_write")
def create_role():
    name = request.form.get("name")
    role = Role(name=name)
    db.session.add(role)
    db.session.commit()
    return jsonify(dict(status="success")), HTTPStatus.CREATED


@api_admin_role.route("/<string:id>", methods=["PUT"])
@swag_from(
    {
        "description": "Update permission for role",
        "tags": ["admin roles"],
        "parameters": [
            {"in": "path", "name": "id", "required": "true", "schema": {"type": "string"}},
            {
                "description": "List of available permissions",
                "in": "body",
                "name": "body",
                "required": "true",
                "schema": {
                    "id": "PermissionNameList",
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.CREATED): {
                "description": "Update role",
            },
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
            int(HTTPStatus.UNAUTHORIZED): {"description": "Unauthorized", "schema": {"type": "string"}},
            int(HTTPStatus.FORBIDDEN): {"description": "Forbidden", "schema": {"type": "string"}},
        },
    }
)
@jwt_required()
@user_has("all_write")
def update_role(id):
    try:
        uuid.UUID(id)
        role = Role.query.filter_by(id=id).one()
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.FORMAT_ERROR)
    except exc.NoResultFound:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.MISSING_USER)
    db.session.query(Permission).filter(Permission.id_role == role.id).delete(synchronize_session=False)
    for permission in request.json:
        logging.debug(permission)
        role.permissions.append(Permission(name=permission))
    db.session.commit()
    return jsonify(dict(status="success")), HTTPStatus.CREATED


@api_admin_role.route("/<string:id>", methods=["DELETE"])
@swag_from(
    {
        "tags": ["admin roles"],
        "parameters": [
            {"in": "path", "name": "id", "required": "true", "schema": {"type": "string", "format": "uuid"}},
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.NO_CONTENT): {
                "description": "Delete role",
            },
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
            int(HTTPStatus.UNAUTHORIZED): {"description": "Unauthorized", "schema": {"type": "string"}},
            int(HTTPStatus.FORBIDDEN): {"description": "Forbidden", "schema": {"type": "string"}},
        },
    }
)
@jwt_required()
@user_has("all_write")
def delete_role(id):
    try:
        uuid.UUID(id)
        role = Role.query.filter_by(id=id).one()
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.FORMAT_ERROR)
    except exc.NoResultFound:
        abort(HTTPStatus.BAD_REQUEST, description=ErrMsgEnum.MISSING_USER)
    db.session.delete(role)
    db.session.commit()
    return jsonify(dict(status="success")), HTTPStatus.NO_CONTENT
