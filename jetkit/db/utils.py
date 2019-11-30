from sqlalchemy.event import listen
from sqlalchemy import Table
from functools import partial


def escape_like(query: str, escape_character: str) -> str:
    """
    Escape special characters that are used in SQL's LIKE and ILIKE.

    Chosen escape character is prepended to each occurrence of a special character.
    Escape character is considered a special character too.

    WARNING: Do not forget to specify escape character to SQLAlchemy when actually
    performing `like`s and `ilike`s:
    >>> escape_character = "~"
    >>> search_query = "99.5%"
    >>> search_query = escape_like(search_query, escape_character)
    >>> Record.query.like(search_query, escape=escape_character) # do not forget `escape`
    """
    assert len(escape_character) == 1
    # It is crucial that `escape_character` is replaced first
    cases = [escape_character, "%", "_"]
    for case in cases:
        query = query.replace(case, escape_character + case)
    return query


def on_table_create(class_, ddl):
    """Run DDL on model class `class_` after creation, whether in migration or in deploy (as in tests)."""

    def listener(tablename, ddl, table, bind, **kw):
        if table.name == tablename:
            ddl(table, bind, **kw)

    listen(Table, "after_create", partial(listener, class_.__table__.name, ddl))
