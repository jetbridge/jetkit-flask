from enum import Enum, unique
from functools import wraps

from sqlalchemy import Column, desc, nullslast
from typing import Iterable, Callable
from flask_jwt_extended import jwt_required, current_user
from flask import request
from flask_smorest import abort, Api, Page

api = Api()


class CursorPage(Page):
    @property
    def item_count(self):
        return self.collection.count_no_subquery()


def permissions_required(permissions: Iterable) -> Callable:
    """
    Decorate functions that require user permissions control.

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


@unique
class SortOrder(Enum):
    desc = "desc"
    asc = "asc"


def sortable_by(*permitted_columns: Column) -> Callable:
    """Permit sorting result of api call.

    Wrapped function needs to return sql query.
    """
    permitted_columns_by_name = {column.name: column for column in permitted_columns}

    def decorator(request_handler):
        @wraps(request_handler)
        def wrapper(*args, **kwargs):
            query = request_handler(*args, **kwargs)

            sort_field_name = request.args.get("sort_by")
            try:
                reverse_parameter = SortOrder(request.args.get("order", "asc"))
            except ValueError:
                abort(
                    400,
                    message=f"'{request.args.get('order')}' is not valid value for 'order'",
                )

            if not sort_field_name:
                return query

            column_to_sort_by = permitted_columns_by_name.get(sort_field_name)
            if column_to_sort_by is None:
                abort(400, message=f"'{sort_field_name}' is not a valid sorting key")

            if reverse_parameter == SortOrder.desc:
                column_to_sort_by = desc(column_to_sort_by)

            return query.order_by(nullslast(column_to_sort_by))

        sorting_keys = ", ".join(f"`{key}`" for key in permitted_columns_by_name.keys())
        append_docs(
            wrapper,
            f"Can be sorted using `?sort_by=`." f" Sorting keys are {sorting_keys}.",
        )

        return wrapper

    return decorator


def combined_search_by(
    *columns: Column, search_parameter_name: str = "search"
) -> Callable:
    """Filter query by filtering on provided columns looking for requested search.

    Wrapped function needs to return sql query.
    """

    def decorator(request_handler):
        @wraps(request_handler)
        def wrapper(*args, **kwargs):
            query = request_handler(*args, **kwargs)
            search_query = request.args.get(search_parameter_name)
            if search_query is None:
                return query

            return query.search(search_query, *columns)

        column_names = ", ".join(f"`{column}`" for column in columns)
        append_docs(wrapper, f"`?{search_parameter_name}=` searches by {column_names}")

        return wrapper

    return decorator


def searchable_by(
    column: Column,
    search_parameter_name: str = None,
    exact_match=False,
    autoname=True,
    autoname_prefix="search_",
) -> Callable:
    """Filter query by filtering on provided columns looking for requested search.

    Wrapped function needs to return sql query.
    """
    fallback_parameter_name = autoname_prefix + column.key if autoname else "search"
    search_parameter_name = search_parameter_name or fallback_parameter_name

    def decorator(request_handler):
        @wraps(request_handler)
        def wrapper(*args, **kwargs):
            query = request_handler(*args, **kwargs)
            search_query = request.args.get(search_parameter_name)

            if search_query is not None:
                if exact_match:
                    query = query.filter(column == search_query)
                else:
                    query = query.search(search_query, column)

            return query

        append_docs(wrapper, f"`?{search_parameter_name}=` searches by `{column}`")

        return wrapper

    return decorator


def append_docs(function: Callable, docstring: str, default_doc: str = ".") -> Callable:
    function.__doc__ = (function.__doc__ or f"{default_doc}\n") + f"\n{docstring}\n"
    return function
