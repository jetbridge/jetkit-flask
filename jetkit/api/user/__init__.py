from flask_jwt_extended import jwt_required
from flask_rest_api import Blueprint
from jetkit.model.user import CoreUser as User
from jetkit.db import db
from marshmallow import Schema
from .schema import UserSchema
from typing import Type

blp = Blueprint("Users", __name__, url_prefix="/api/user")


def CoreUserAPI(user_model: User, user_schema: Type[Schema] = UserSchema):
    @blp.route("")
    @blp.response(user_schema(many=True))
    # TODO: protect with @permissions_required
    def get_list():
        """List users."""
        return user_model.query

    @blp.route("<int:user_id>", methods=["GET"])
    @blp.response(user_schema)
    @jwt_required
    def get_user(user_id: int) -> User:
        """Get user details"""
        user = user_model.query.get_or_404(user_id)
        return user

    @blp.route("<int:user_id>", methods=["DELETE"])
    @jwt_required
    def delete_user(user_id: int) -> str:
        """Soft delete user"""
        user = user_model.query.get_or_404(user_id)
        user.mark_deleted()
        db.session.commit()
        return "Ok"
