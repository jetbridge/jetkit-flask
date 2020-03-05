import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from jetkit.db import BaseModel, BaseQuery

TEST_CONFIG = dict(
    TESTING=True,
    SECRET_KEY="testing",
    EMAIL_ENABLED=True,
    EMAIL_SUPPORT="mischa@jetbridge.com",
    EMAIL_API_KEY="fake-api-key",
    EMAIL_DOMAIN="jetbridge.com",
    EMAIL_DEFAULT_SENDER="notifications@jetbridge.com",
)

db = SQLAlchemy(model_class=BaseModel, query_class=BaseQuery)


def create_app(config: dict = None) -> Flask:
    if not config:
        config = {}

    app = Flask("jetkit_test")

    # override config for test app
    app.config.update(dict(**TEST_CONFIG, **config))

    # jwt initialization
    jwt = JWTManager(app)  # noqa F841

    @jwt.user_loader_callback_loader
    def user_loader_callback(identity):
        from jetkit.test.model.user import User

        if identity is None:
            return None
        return User.query.get(identity)

    @jwt.user_loader_error_loader
    def custom_user_loader_error(identity):
        ret = {"msg": f"User {identity} not found"}
        from flask import jsonify

        return jsonify(ret), 404

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        assert user.id
        return user.id

    db.init_app(app)  # init sqlalchemy

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app


@pytest.fixture()
def api_auth(app):
    from jetkit.api.auth import blp, use_core_auth_api, use_sign_up_api
    from jetkit.test.model.user import User

    use_core_auth_api(auth_model=User)
    use_sign_up_api(auth_model=User)
    app.register_blueprint(blp)


@pytest.fixture()
def api_user(app):
    from jetkit.api.user import blp, use_core_user_api
    from jetkit.test.model.user import User

    use_core_user_api(user_model=User)
    app.register_blueprint(blp)
