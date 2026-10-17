from dataclasses import dataclass

from sqlmodel import SQLModel

from atlas.entities import Asset, AssetType, Site

EARLIEST_TIMEZONE = "Pacific/Pago_Pago"
LATEST_TIMEZONE = "Pacific/Kiritimati"


class MissingPersistedIdError(Exception):
    """
    Raised when a test entity was expected to be saved but has no id.
    """
    pass


@dataclass
class Environment:
    """
    The sites, asset types, and assets every test starts with.
    """
    north_site: Site
    south_site: Site
    island_site: Site
    quiet_site: Site
    empty_site: Site
    archived_site: Site
    pump: AssetType
    fan: AssetType
    boiler: AssetType
    valve: AssetType
    archived_asset_type: AssetType
    compressor: Asset
    generator: Asset
    retired_conveyor: Asset
    island_fan: Asset
    archived_boiler: Asset


def get_persisted_id(entity: SQLModel) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise MissingPersistedIdError(f"{entity!r} has no id.")

    return entity_id
