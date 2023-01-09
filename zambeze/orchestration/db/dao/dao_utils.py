from sqlalchemy import text, create_engine

from zambeze.config import LOCAL_DB_SCHEMA, LOCAL_DB_FILE
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity


def create_local_db() -> None:
    with get_db_engine() as connection:
        # conn = get_db_engine()
        with open(LOCAL_DB_SCHEMA) as f:
            connection.execute(text(f.read()))


def get_db_engine():
    try:
        db_uri = f"sqlite:///{LOCAL_DB_FILE}"
        engine = create_engine(db_uri)
        return engine
    except Exception:
        raise Exception(f"Could not create DB engine with uri: {db_uri}")


def get_update_stmt(entity: AbstractEntity):
    stmt = f"UPDATE {entity.ENTITY_NAME} SET \n"
    for field_name in entity.FIELD_NAMES.split(","):
        if field_name == entity.ID_FIELD_NAME:
            continue
        stmt += f"{field_name} = ?, "
    stmt = stmt[:-2]
    id_value = entity.__getattribute__(entity.ID_FIELD_NAME)
    stmt += f" \n WHERE {entity.ID_FIELD_NAME} = {id_value}"
    return stmt


def get_insert_stmt(entity: AbstractEntity):
    number_of_fields = len(entity.FIELD_NAMES.split(","))
    values_replacer = ",".join(["?" for _ in range(number_of_fields)])
    return (
        f"INSERT INTO {entity.ENTITY_NAME} "
        f"({entity.FIELD_NAMES}) VALUES ({values_replacer}); "
    )
