from jetkit.db.utils import on_table_create
from jetkit.db import Model, db
from sqlalchemy.schema import DDL


def test_on_table_create(session):
    class MyTable(Model):
        __tablename__ = "my_table"

    ran_ddl = False

    def handler(*a, **kw):
        nonlocal ran_ddl
        ran_ddl = True

    # install table after_create handlers
    on_table_create(MyTable, handler)
    on_table_create(MyTable, DDL("INSERT INTO my_table (id) VALUES (42); COMMIT"))

    # create table
    Model.metadata.create_all(
        session.connection().engine,
        [Model.metadata.tables["my_table"]],
        checkfirst=True,
    )

    # verify handlers ran
    assert session.query(MyTable).first().id == 42
    assert ran_ddl
