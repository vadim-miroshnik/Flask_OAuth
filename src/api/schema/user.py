"""User schema"""

from marshmallow import Schema, fields

from ..schema.role import RoleSchema


class UserSchema(Schema):
    class Meta:
        fields = [
            "id",
            "login",
            "password",
            "role",
        ]

    id = fields.Str(description="Id", required=True)
    login = fields.Str(description="Login", required=True)
    role = fields.Nested(RoleSchema, many=True)
    password = fields.Str(description="Password", required=True)


class UsersSchema(Schema):
    class Meta:
        fields = ["users"]

    users = fields.Nested(UserSchema, many=True)
