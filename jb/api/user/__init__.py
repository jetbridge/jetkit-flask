from flask_rest_api import Blueprint, abort
from marshmallow import fields as f, Schema
from flask_jwt_extended import jwt_required
from abc import abstractmethod
from sqlalchemy.orm import Query

from jb.model.user import CoreUser as User
from .schema import UserSchema

blp = Blueprint(
    'Users',
    __name__,
    url_prefix='/api/users',
)


def CoreUserAPI(user_schema: Schema = UserSchema):
    @blp.route('')
    @jwt_required
    @blp.response(user_schema(many=True))
    # TODO: protect with @permissions_required
    def get(self):
        """List users."""
        return User.query

    @blp.route('<int:user_id>', methods=['GET'])
    @blp.response(user_schema)
    @jwt_required
    def get_user(user_id: int) -> User:
        """Get user details"""
        user = User.query.get_or_404(user_id)
        return user
