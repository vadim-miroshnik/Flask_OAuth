import unittest
from avro.datafile import DataFileReader
from avro.io import DatumReader
from app import app
from core.settings import settings


class TestUsersInterract(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_steps(self):
        with self.client:
            response = self.client.get(
                "/api/inter/user/", content_type="application/json"
            )

            self.assertEqual(response.status_code, 200)
            with open('users.avro', "wb") as file:
                file.write(response.data)
            reader = DataFileReader(open('users.avro', 'rb'), DatumReader())
            users_by_dict = {user_data['name']: user_data for user_data in reader}
            self.assertTrue(users_by_dict)
            self.assertIn(settings.superuser.username, users_by_dict)
            superuser = users_by_dict[settings.superuser.username]
            self.assertEqual(settings.superuser.email, superuser['email'])



if __name__ == "__name__":
    unittest.main()
