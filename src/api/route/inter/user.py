from http import HTTPStatus

from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from avro.schema import make_avsc_object
from flasgger import swag_from
from flask import send_from_directory, Blueprint

from avro_schemes.user_avro_scheme import user as user_avro_scheme
from core.settings import settings
from models.db_models import User

inter_user = Blueprint("inter_user", __name__)


@inter_user.route("/", methods=["GET"])
@swag_from(
    {
        "tags": ["interraction"],
        "responses": {
            int(HTTPStatus.OK): {"description": "Get roles", "schema": {"type": "file"}},
            int(HTTPStatus.BAD_REQUEST): {"description": "Bad request", "schema": {"type": "string"}},
        },
    }
)
def user_avro():
    parsed_schema = make_avsc_object(user_avro_scheme)
    scheme_file = settings.avro_path.joinpath("users.avro_schemes")
    writer = DataFileWriter(open(scheme_file, "wb"), DatumWriter(), parsed_schema)
    for user in User.query.all():
        writer.append({"name": user.login, "pk": str(user.id), "email": user.email if user.email else ""})
    writer.close()
    return send_from_directory(settings.avro_path, "users.avro_schemes")

