"""Signin schema"""

from marshmallow import Schema, fields


class SignInSchema(Schema):
    class Meta:
        fields = [
            "login",
            "password",
        ]

    login = fields.Str(description="Login", required=True)
    password = fields.Str(description="Password", required=True)
