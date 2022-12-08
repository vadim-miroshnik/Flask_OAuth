"""Permission schema"""

from marshmallow import Schema, fields

import models.db_models


class PermissionSchema(Schema):
    class Meta:
        fields = ["name", "permission_descriptions"]

    name = fields.Enum(models.db_models.PermissionType, description="Name", required=True, by_value=False)


class PermissionSchemaInfo(Schema):
    class Meta:
        fields = ["name"]

    name = fields.String(description="Name")
