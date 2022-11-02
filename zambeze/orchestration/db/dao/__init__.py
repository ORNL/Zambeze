from sqlalchemy import create_engine, text

from zambeze.config import LOCAL_DB_FILE, LOCAL_DB_SCHEMA

from zambeze.orchestration.db.model.abstract_entity import AbstractEntity


def create_local_db() -> None:
    conn = get_db_engine()
    with open(LOCAL_DB_SCHEMA) as f:
        conn.execute(
            text(f.read())
        )


def get_db_engine():
    try:
        db_uri = f"sqlite:///{LOCAL_DB_FILE}"
        engine = create_engine(db_uri)
        return engine
    except Exception:
        raise Exception(f"Could not create DB engine with uri: {db_uri}")


def get_update_stmt_from_entity_object(entity: AbstractEntity):
    stmt = f"UPDATE {entity.ENTITY_NAME} SET \n"
    for field_name in entity.FIELD_NAMES.split(','):
        if field_name == entity.ID_FIELD_NAME:
            continue
        stmt += f"{field_name} = ?, "
    stmt = stmt[:-2]
    id_value = entity.__getattribute__(entity.ID_FIELD_NAME)
    stmt += f" \n WHERE {entity.ID_FIELD_NAME} = {id_value}"
    return stmt


def get_insert_stmt(entity_name: str, field_names):
    number_of_fields = len(field_names.split(','))
    values_replacer = ",".join(['?' for _ in range(number_of_fields)])
    return f"INSERT INTO {entity_name} " \
           f"({field_names}) VALUES ({values_replacer}); "

# def get_insert_returning_stmt(entity_name: str, field_names, id_field_name: str):
#     number_of_fields = len(field_names.split(','))
#     values_replacer = ",".join(['?' for _ in range(number_of_fields)])
#     return f"INSERT INTO {entity_name} " \
#            f"({field_names}) VALUES ({values_replacer}) " \
#            f"RETURNING {id_field_name}; "


# def get_update_stmt_from_dict(entity_name, new_values: Dict, id_field_name, id_field_value):
#     stmt = f"UPDATE {entity_name} SET \n"
#     for field_name in new_values:
#         stmt += f"{field_name} = ?, "
#     stmt = stmt[:-2]
#     stmt += f" \n WHERE {id_field_name} = {id_field_value}"
#     return stmt
