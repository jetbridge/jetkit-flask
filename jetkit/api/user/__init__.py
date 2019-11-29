from flask_jwt_extended import jwt_required
from flask_rest_api import Blueprint
from jetkit.model.user import CoreUser as User
from marshmallow import Schema
from sqlalchemy.orm import Query

from .schema import UserSchema

blp = Blueprint("Users", __name__, url_prefix="/api/user")


# user model protocol
class UserModel:
    id: int
    query: Query


def CoreUserAPI(user_model: UserModel, user_schema: Schema = UserSchema):
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
