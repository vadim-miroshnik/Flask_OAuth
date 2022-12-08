"""Permissions endpoints"""

import logging
from http import HTTPStatus

from flasgger import swag_from
from flask import Blueprint
from flask_jwt import jwt_required

from api.route.static import swagger_param_auth_token
from api.schema.permission import PermissionSchema, PermissionSchemaInfo
from models.db_models import PermissionType

api_admin_permission = Blueprint("admin_permission", __name__)


@api_admin_permission.route("/")
@swag_from(
    {
        "tags": ["permission"],
        "parameters": [
            swagger_param_auth_token,
        ],
        "responses": {
            int(HTTPStatus.OK): {
                "description": "Available permissions",
                "schema": {"id": "PermissionList", "type": "array", "items": PermissionSchemaInfo},
            }
        },
    }
)
@jwt_required()
def get_permissions():
    permissions = PermissionSchema(many=True).dump([{"name": permission} for permission in PermissionType])
    logging.debug("%s", permissions)
    return permissions, HTTPStatus.OK
