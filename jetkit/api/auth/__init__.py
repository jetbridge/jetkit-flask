from flask_smorest import Blueprint, abort
from marshmallow import fields as f, Schema
from flask_jwt_extended import (
    jwt_required,
    jwt_refresh_token_required,
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from abc import abstractmethod
from sqlalchemy.orm import Query
from jetkit.api.user.schema import UserSchema
from typing import Type
from jetkit.model.user import CoreUser as User
from sqlalchemy.dialects.postgresql import insert as pg_insert
from ...model.user import CoreUserType
from werkzeug.security import generate_password_hash

blp = Blueprint("Authentication", __name__, url_prefix="/api/auth")


# default schemas
class LoginRequest(Schema):
    password = f.String(required=True, allow_none=False)
    email = f.String(required=True, allow_none=False)


class SignUpResponse(Schema):
    extid = f.String(dump_only=True, data_key="id")
    name = f.String()
    email = f.Email()
    dob = f.Date()
    phone_number = f.String()


class AuthResponse(Schema):
    access_token = f.String()
    refresh_token = f.String()
    user = f.Nested(SignUpResponse)


class RefreshTokenResponse(Schema):
    access_token = f.String()


# auth model protocol
class AuthModel:
    id: int
    email: str
    password: str

    # assuming for flask-sqlalchemy
    query: Query

    @abstractmethod
    def is_correct_password(self, pw: str) -> bool:
        raise NotImplementedError()


@blp.response(AuthResponse)
def auth_response_for_user(user: AuthModel) -> dict:
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return {
        "access_token": access_token,  # valid for 15 minutes by default
        "refresh_token": refresh_token,  # valid for 30 days by default
        "user": user,
    }


def use_core_auth_api(auth_model: AuthModel, user_schema: Type[Schema] = UserSchema):
    @blp.route("login", methods=["POST"])
    @blp.arguments(LoginRequest, as_kwargs=True)
    def login(email: str, password: str):
        """Login with email + password."""
        cleaned_email = email.strip().lower()
        user: AuthModel = auth_model.query.filter_by(email=cleaned_email).one_or_none()
        if not user or not user.password or not user.is_correct_password(password):
            abort(401, message="Wrong user name or password")
        return auth_response_for_user(user)

    @blp.route("sign-up", methods=["POST"])
    @blp.response(SignUpResponse)
    @blp.arguments(LoginRequest, as_kwargs=True)
    def sign_up(email: str, password: str):
        """Sign up with email and password. Possibly add other fields later."""
        cleaned_email = email.strip().lower()
        existing_user: AuthModel = auth_model.query.filter_by(email=cleaned_email).one_or_none()
        if existing_user:
            abort(400, message="There's already a registered user with such email")
        values = dict(email=email, _password=generate_password_hash(password), _user_type=CoreUserType.normal.value)
        new_user = User.upsert_row(
            auth_model,
            values=values,
            index_elements=["id"]
        )
        auth_model.query.session.commit()
        return new_user

    @blp.route("check", methods=["GET"])
    @jwt_required
    def check_user():
        """Check if current access token is valid."""
        return "ok"

    @blp.route("refresh", methods=["POST"])
    @jwt_refresh_token_required
    @blp.response(RefreshTokenResponse)
    def refresh_token():
        current_user = get_current_user()
        return {"access_token": create_access_token(identity=current_user)}
