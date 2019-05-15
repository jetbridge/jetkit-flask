# from flask_rest_api import Blueprint, abort
# from marshmallow import fields as f, Schema
# from flask_jwt_extended import jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity
# from abc import abstractmethod
# from sqlalchemy.orm import Query

# from flask.views import MethodView

# from businessrocket.model.company import Company
# from .schema import UserSchema
# from flask_jwt_extended import jwt_required

# blp = Blueprint(
#     'Users',
#     __name__,
#     url_prefix='/api/users',
# )


# @blp.route('')
# class CompanyAPI(MethodView):
#     @blp.response(CompanySchema(many=True))
#     def get(self):
#         """List companies."""
#         return Company.query


# @blp.route('<int:company_id>', methods=['GET'])
# @blp.response(CompanySchema)
# @jwt_required
# def get_company(company_id: int) -> Company:
#     """Get company details"""
#     company = Company.query.get_or_404(company_id)
#     return company


# def CoreAuthAPI(auth_model: AuthModel, user_schema: Schema = UserSchema):
#     class AuthResponse(Schema):
#         access_token = f.String(dump_only=True)
#         refresh_token = f.String(dump_only=True)
#         user = f.Nested(user_schema)

#     @blp.route('login', methods=['POST'])
#     @blp.response(AuthResponse)
#     @blp.arguments(LoginRequest, as_kwargs=True)
#     def login(email: str, password: str):
#         """Login with email + password."""
#         cleaned_email = email.strip().lower()
#         user: AuthModel = auth_model.query\
#                                     .filter_by(email=cleaned_email).one_or_none()
#         if not user or not user.password or not user.is_correct_password(password):
#             abort(401, message="Wrong user name or password")
#         return auth_response_for_user(user)

#     @blp.route('check', methods=['GET'])
#     @jwt_required
#     def check_user():
#         """Check if current access token is valid."""
#         return "ok"

#     # endpoint is reachable only if refresh_token is present and valid
#     # access_token itself doesn't provide access to this endpoint
#     @blp.route('refresh', methods=['GET'])
#     @jwt_refresh_token_required
#     @blp.response(RefreshTokenResponse)
#     def refresh_tokens():
#         """Generate new tokens if current user has valid refresh token"""
#         return refresh_token_response(get_jwt_identity())
