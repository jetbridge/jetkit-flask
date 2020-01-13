from jetkit.db.utils import on_table_create
from jetkit.test.app import db
from sqlalchemy.schema import DDL


def test_on_table_create(session):
    model_cls = db.Model

    class MyTable(model_cls):
        __tablename__ = "my_table"

    ran_ddl = False

    def handler(*a, **kw):
        nonlocal ran_ddl
        ran_ddl = True

    # install table after_create handlers
    on_table_create(MyTable, handler)
    on_table_create(MyTable, DDL("INSERT INTO my_table (id) VALUES (42); COMMIT"))

    # create table
    model_cls.metadata.create_all(
        session.connection().engine,
        [model_cls.metadata.tables["my_table"]],
        checkfirst=True,
    )

    # verify handlers ran
    assert session.query(MyTable).first().id == 42
    assert ran_ddl


def test_update_attributes(user):
    # TODO: test subfield updates
    user.update(name="fred")
    assert user.name == "fred"
