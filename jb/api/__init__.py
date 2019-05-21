from flask_rest_api import Api
from functools import wraps
from typing import Iterable
from flask_jwt_extended import jwt_required, current_user
from flask import abort

api = Api()


def permissions_required(permissions: Iterable):
    """
    Use this as a decorator to functions that require user permissions control
    Pass permissions as a list of UserType enum values
    """
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated_function(*args, **kwargs):
            if current_user.user_type not in permissions:
                abort(404)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
