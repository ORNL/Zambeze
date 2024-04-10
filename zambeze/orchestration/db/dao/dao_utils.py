from textwrap import dedent
from sqlalchemy import text, create_engine

from zambeze.config import LOCAL_DB_SCHEMA, LOCAL_DB_FILE
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity


def create_local_db() -> None:
    eng = get_db_engine()

    with open(LOCAL_DB_SCHEMA) as f:
        ff = f.read()

    with eng.connect() as conn:
        conn.execute(text(ff))


def get_db_engine():
    db_uri = f"sqlite:///{LOCAL_DB_FILE}"
    try:
        engine = create_engine(db_uri)
        return engine
    except Exception:
        raise Exception(f"Could not create DB engine with uri: {db_uri}")


def get_update_stmt(entity: AbstractEntity) -> str:
    field_names = entity.FIELD_NAMES.split(", ")
    x = [f"{name}=:{name}" for name in field_names if name != "activity_id"]
    names = ", ".join(x)

    id_value = entity.__getattribute__(entity.ID_FIELD_NAME)

    stmt = f"""UPDATE {entity.ENTITY_NAME}
    SET {names}
    WHERE {entity.ID_FIELD_NAME} = {id_value}"""

    return dedent(stmt)


def get_insert_stmt(entity: AbstractEntity) -> str:
    field_names = entity.FIELD_NAMES
    names = ", ".join([":" + name for name in field_names.split(", ")])
    stmt = f"INSERT INTO {entity.ENTITY_NAME} ({entity.FIELD_NAMES}) VALUES ({names})"
    return stmt
