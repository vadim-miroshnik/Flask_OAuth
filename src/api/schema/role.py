"""Role schema"""

from marshmallow import Schema, fields

from api.schema.permission import PermissionSchema, PermissionSchemaInfo


class RoleSchema(Schema):
    class Meta:
        fields = ["id", "name", "permissions"]

    id = fields.Str(description="Id", required=True, format="uuid")
    name = fields.Str(description="Name", required=True)
    permissions = fields.List(fields.Nested(PermissionSchema))


class RoleSchemaInfo(Schema):
    class Meta:
        fields = ["id", "name", "permissions"]

    id = fields.Str(description="Id", required=True, format="uuid")
    name = fields.Str(description="Name", required=True)
    permissions = fields.List(fields.Nested(PermissionSchemaInfo))
