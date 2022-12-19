"""Application"""

from flasgger import Swagger
from flask import Flask, jsonify
from flask_jwt import JWT
from flask_migrate import Migrate

from api.route.crud import api_admin_permission, api_admin_role, api_admin_user
from api.route.inter.user import inter_user
from api.route.users import users_api
from api.route.oauth import google_blueprint
from core.db import db
from core.login_manager import authenticate, identity, login_manager
from core.redis import redis
from core.settings import AppSettings

app = Flask(__name__, subdomain_matching=True)
app.config.from_object(AppSettings)
swagger = Swagger(app)
migrate = Migrate(app, db)

app.register_blueprint(users_api, url_prefix="/api/users")
app.register_blueprint(google_blueprint, url_prefix="/api/users/login")
app.register_blueprint(api_admin_user, url_prefix="/api/admin/user")
app.register_blueprint(api_admin_role, url_prefix="/api/admin/role")
app.register_blueprint(api_admin_permission, url_prefix="/api/admin/permission")
app.register_blueprint(inter_user, url_prefix="/api/inter/user")


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(401)
def unauthorized(e):
    return jsonify(error=str(e)), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify(error=str(e)), 403


db.init_app(app)
redis.init_app(app)

jwt = JWT(app, authenticate, identity)
login_manager.init_app(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
