from sqlmodel import SQLModel


class MissingPersistedIdError(Exception):
    """
    Raised when a test entity was expected to be saved but has no id.
    """
    pass


def get_persisted_id(entity: SQLModel) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise MissingPersistedIdError(f"{entity!r} has no id.")

    return entity_id
