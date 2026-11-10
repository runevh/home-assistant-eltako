"""Keep v1 entity IDs and user settings when adopting v2 unique IDs."""
import re

from eltakobus.util import AddressExpression
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er

from ..config.config_helpers import get_device_id
from ..const import DOMAIN, LOGGER

_LEGACY_ID = re.compile(r'^eltako_gw(\d+)_((?:[0-9a-f]{2}_){3}[0-9a-f]{2})(?:_(.*))?$')


def replacement_unique_id(unique_id: str, gateway_id: int) -> str | None:
    """Translate only the known v1 format for this gateway, including radio devices."""
    match = _LEGACY_ID.fullmatch(unique_id)
    if match is None or int(match[1]) != gateway_id:
        return None
    address = AddressExpression.parse(match[2].replace('_', '-'))
    return get_device_id(gateway_id, address, match[3])


def migrate_entity_registry(registry, config_entry_id: str | None, gateway_id: int) -> int:
    """Preflight every mapping before changing unique IDs; never rename entities.

    Conflicts need explicit resolution: silently choosing a duplicate can lose the
    original entity's history, area, custom name or disabled setting.
    """
    changes = []
    targets = set()
    for entry in list(registry.entities.values()):
        if entry.platform != DOMAIN or entry.config_entry_id != config_entry_id:
            continue
        unique_id = replacement_unique_id(entry.unique_id, gateway_id)
        if unique_id is None:
            continue
        domain = entry.entity_id.split('.', 1)[0]
        key = (domain, unique_id)
        existing = registry.async_get_entity_id(domain, DOMAIN, unique_id)
        if key in targets or (existing is not None and existing != entry.entity_id):
            raise ConfigEntryError(
                f"Eltako migration conflict for {entry.entity_id}: {unique_id} already exists. "
                "Restore the pre-upgrade registry or resolve the duplicate before retrying."
            )
        targets.add(key)
        changes.append((entry.entity_id, unique_id))
    for entity_id, unique_id in changes:
        registry.async_update_entity(entity_id, new_unique_id=unique_id)
    return len(changes)


def async_migrate_legacy_entities(hass, config_entry_id: str, gateway_id: int) -> None:
    """Run on the HA event loop before creating gateway platforms."""
    count = migrate_entity_registry(er.async_get(hass), config_entry_id, gateway_id)
    if count:
        LOGGER.info("Migrated %s Eltako unique IDs while preserving entity IDs and settings", count)
