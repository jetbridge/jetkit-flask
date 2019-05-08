from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import DateTime, Integer, func, Column, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Any, Dict


TSTZ = DateTime(timezone=True)


# our base model
class DeclarativeBase(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer(), primary_key=True)
    created = Column(TSTZ, nullable=False, server_default=func.now())
    updated = Column(TSTZ, nullable=True, onupdate=func.now())
Base = declarative_base(cls=DeclarativeBase)
Session = sessionmaker()


def configure_session_url(db_url: str):
    engine = create_engine(db_url, echo=True)
    configure_session_engine(engine)


def configure_session_engine(engine):
    Session.configure(bind=engine)


# model mixin
class Upsertable():
    """Model mixin to provide postgres upsert capability."""

    @classmethod
    def upsert_row(cls,
                   row_class,
                   *,
                   index_elements: List[str] = None,
                   constraint=None,
                   set_: Dict[str, Any],
                   should_return_result=True,
                   values: Dict[str, Any]):
        """Insert or update if index_elements match.

        N.B. does not commit.

        :set_: sets values if exists
        :values: are inserted if not exists
        :should_return_result: if false will not return object and will not do commit
        :returns: model fetched from DB.
        """
        session = Session()

        # what do we detect conflict on?
        conflict = None
        if index_elements:
            conflict = {'index_elements': index_elements}
        elif constraint:
            conflict = {'constraint': constraint}
        else:
            raise Exception("constraint or index_elements must be specified")

        insert_query = pg_insert(row_class).on_conflict_do_update(
            **conflict,
            set_=set_,
        ).values(**values)
        res = session.execute(insert_query)
        if not should_return_result:
            return None
        assert res  # we always get a result if the query completes successfully right?
        id = res.inserted_primary_key[0]
        result = row_class.query.get(id)
        assert result
        session.commit()
        return result
