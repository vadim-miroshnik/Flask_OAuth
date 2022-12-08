"""Login schema"""

from marshmallow import Schema, fields


class LoginSchema(Schema):
    class Meta:
        fields = [
            "dt",
            "login",
            "ip",
            "user_agent",
        ]

    dt = fields.Str(description="DT", required=True)
    login = fields.Str(description="Login", required=True)
    ip = fields.Str(description="IP address", required=True)
    user_agent = fields.Str(description="User Agent", required=True)


class LoginsSchema(Schema):
    class Meta:
        fields = ["logins"]

    logins = fields.Nested(LoginSchema, many=True)
