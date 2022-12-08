"""Error messages"""

from enum import Enum


class ErrMsgEnum(str, Enum):
    LOGIN_EXISTS = "Login already exists"
    PASSWORD_ERROR = "Password must have more than 6 symbols"
    CONTENT_NOT_SUPPORTED = "Content-Type not supported"
    INPUT_ERROR = "Input login and password"
    LOGIN_NOT_EXISTS = "Login does not exists"
    PASSWORD_NOT_MATCH = "Password does not match"
    NO_REFRESH_TOKEN = "No refresh token"
    FORMAT_ERROR = "Incorrect format ID"
    MISSING_USER = "Missing user"
    MISSING_ROLE = "Missing role"
