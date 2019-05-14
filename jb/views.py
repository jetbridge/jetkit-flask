"""
All views and APIs.

Load all views and export all blueprints for the app in this file.
"""
from .api.auth import blp as auth_blueprint

register_blueprints = (
    auth_blueprint,
)
