from typing import Any, Dict, List, Optional
from flask_sqlalchemy import Model
from sqlalchemy.dialects.postgresql import insert as pg_insert


class Upsertable:
    @classmethod
    def upsert_row(
        cls,
        row_class,
        *,
        index_elements: List[str] = None,
        constraint=None,
        set_: Dict[str, Any] = None,
        should_return_result=True,
        values: Dict[str, Any],
    ) -> Optional[Model]:  # noqa T484
        """Insert or update if index_elements match.

        :set_: sets values if exists
        :values: are inserted if not exists
        :should_return_result: if false will not return object and will not do commit
        :returns: model fetched from DB.
        """
        if not set_:
            set_ = values

        # what do we detect conflict on?
        conflict = None
        if index_elements:
            conflict = {"index_elements": index_elements}
        elif constraint:
            conflict = {"constraint": constraint}
        else:
            raise Exception("constraint or index_elements must be specified")

        # create INSERT ... ON CONFLICT DO UPDATE statement
        insert_query = (
            pg_insert(row_class)
            .on_conflict_do_update(**conflict, set_=set_)
            .values(**values)
        )

        session = row_class.query.session

        # execute insert
        res = session.execute(insert_query)
        if not should_return_result:
            # if we don't care about getting the inserted object, we can stop now
            return None

        # retrieve inserted row
        assert res
        inserted_id = res.inserted_primary_key[0]
        assert inserted_id
        result = row_class.query.get(inserted_id)
        assert result
        session.expire(result)
        return result
