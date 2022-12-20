"""Unittest"""

import base64
import json
import secrets
import string
import unittest

import jwt

from app import app
from core.settings import settings

alphabet = string.ascii_letters + string.digits
login = "".join(secrets.choice(alphabet) for _ in range(6))
password = "".join(secrets.choice(alphabet) for _ in range(6))
access_token = ""
refresh_token = ""


class TestUsers(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def step_01_registration(self):
        global access_token
        global refresh_token
        with self.client:
            response = self.client.post(
                "api/users/register",
                data=json.dumps(dict(login=login, password=password)),
                content_type="application/json",
            )
            data = json.loads(response.data.decode())
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            payload = jwt.decode(
                data["access_token"], key=base64.b64decode(settings.app.jwt_secret_key), algorithms=["HS256"]
            )
            self.assertTrue(payload["role"] == "user")
            self.assertTrue(response.content_type == "application/json")
            self.assertEqual(response.status_code, 201)

    def step_02_login_correct(self):
        with self.client:
            response = self.client.post(
                "api/users/login",
                data=json.dumps(dict(login=login, password=password)),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 201)

    def step_03_login_not_correct(self):

        with self.client:
            response = self.client.post(
                "api/users/login",
                data=json.dumps(dict(login=login, password=password + "_")),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def step_04_update_password(self):
        global login
        global password
        global access_token
        global refresh_token
        password = password + "_"
        with self.client:
            response = self.client.put(
                "api/users/profile",
                headers={"Authorization": "JWT " + access_token, },
                data=json.dumps(dict(login=login, password=password)),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 201)

    def step_05_refresh(self):
        global access_token
        global refresh_token
        with self.client:
            response = self.client.post(
                "api/users/refresh",
                data=refresh_token,
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)

    def step_06_login_history(self):
        global access_token
        with self.client:
            response = self.client.get(
                "api/users/history/1",
                headers={"Authorization": "JWT " + access_token, },
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data.decode())
            logins = data["logins"]
            self.assertTrue(len(logins) > 0)

    def step_07_logout(self):
        global access_token
        with self.client:
            response = self.client.post(
                "api/users/logout",
                headers={"Authorization": "JWT " + access_token, },
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 201)

    def steps(self):
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        for name, step in self.steps():
            try:
                step()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(step, type(e), e))


if __name__ == "__name__":
    unittest.main()
