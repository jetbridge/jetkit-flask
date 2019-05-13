from flask_rest_api import Blueprint, abort
from marshmallow import fields as f, Schema
# from jb.db import Session
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity
from abc import abstractmethod
from sqlalchemy.orm import Query

blp = Blueprint(
    'Authentication',
    __name__,
    url_prefix='/api/auth',
)


# default schemas
class LoginRequest(Schema):
    password = f.String(required=True, allow_none=False)
    email = f.String(required=True, allow_none=False)


# FIXME: move to user schemas
class CoreUserSchema(Schema):
    id = f.Integer()
    name = f.String()
    email = f.String()
    dob = f.Date()
    phone_number = f.String()


class AuthResponse(Schema):
    access_token = f.String()
    refresh_token = f.String()
    user = f.Nested(CoreUserSchema)


class RefreshTokenResponse(Schema):
    access_token = f.String()


# auth model protocol
class AuthModel():
    id: int
    email: str
    password: str

    # assuming for flask-sqlalchemy (for now)
    query: Query

    @abstractmethod
    def is_correct_password(self, pw: str) -> bool:
        raise NotImplementedError()


def refresh_token_response(user: int) -> dict:
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return {'access_token': access_token, 'refresh_token': refresh_token}


def auth_response_for_user(user: AuthModel) -> dict:
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return {
        'access_token': access_token,  # valid for 15 minutes by default
        'refresh_token': refresh_token,  # valid for 30 days by default
        'user': user,
    }


class CoreAuth:
    auth_model: AuthModel

    @classmethod
    def login(cls, email: str, password: str):
        """Login with email + password."""
        # session = Session()

        cleaned_email = email.strip().lower()
        user: AuthModel = cls.auth_model.query\
                                        .filter_by(email=cleaned_email).one_or_none()
        if not user or not user.password or not user.is_correct_password(password):
            abort(401, message="Wrong user name or password")
        return auth_response_for_user(user)

    @classmethod
    @jwt_required
    @blp.response(schema=None, code=401, description="Invalid access token.")
    def check_user(cls):
        """Check if current access token is valid."""
        return "ok"

    # endpoint is reachable only if refresh_token is present and valid
    # access_token itself doesn't provide access to this endpoint
    @classmethod
    @jwt_refresh_token_required
    @blp.response(RefreshTokenResponse)
    def refresh_tokens(cls):
        """Generate new tokens if current user has valid refresh token"""
        return refresh_token_response(get_jwt_identity())
