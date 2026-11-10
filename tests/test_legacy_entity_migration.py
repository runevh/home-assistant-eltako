"""Migration preserves automation targets and refuses ambiguous duplicates."""
from dataclasses import dataclass, replace
import unittest

from homeassistant.exceptions import ConfigEntryError
from custom_components.eltako.core.entity_migration import migrate_entity_registry, replacement_unique_id


@dataclass(frozen=True)
class Entry:
    entity_id: str
    unique_id: str
    config_entry_id: str = 'gateway-one'
    platform: str = 'eltako'
    disabled_by: str | None = None
    name: str = 'Custom room name'
    area_id: str = 'living_room'


class Registry:
    def __init__(self, entries):
        self.entities = {e.entity_id: e for e in entries}

    def async_get_entity_id(self, domain, platform, unique_id):
        return next((e.entity_id for e in self.entities.values()
                     if e.entity_id.startswith(domain + '.') and e.platform == platform
                     and e.unique_id == unique_id), None)

    def async_update_entity(self, entity_id, *, new_unique_id):
        self.entities[entity_id] = replace(self.entities[entity_id], unique_id=new_unique_id)


class TestLegacyEntityMigration(unittest.TestCase):
    def test_preserves_heating_lighting_cover_and_priority_entity_settings(self):
        entries = [Entry(f'{domain}.my_existing_name', 'eltako_gw1_00_00_00_47',
                         disabled_by='user' if domain == 'cover' else None)
                   for domain in ('climate', 'select', 'light', 'cover')]
        registry = Registry(entries)
        self.assertEqual(migrate_entity_registry(registry, 'gateway-one', 1), 4)
        for entry in entries:
            migrated = registry.entities[entry.entity_id]
            self.assertEqual(migrated, replace(entry, unique_id='eltako_gw_1_00_00_00_47'))
        self.assertEqual(migrate_entity_registry(registry, 'gateway-one', 1), 0)

    def test_radio_and_description_suffix(self):
        self.assertEqual(replacement_unique_id('eltako_gw1_ff_aa_00_01_temperature', 1),
                         'eltako_ff_aa_00_01_temperature')
        self.assertEqual(replacement_unique_id('eltako_gw1_00_00_00_47_id', 1),
                         'eltako_gw_1_00_00_00_47_id')

    def test_other_entries_and_platforms_are_untouched(self):
        entries = [Entry('light.other_entry', 'eltako_gw1_00_00_00_01', config_entry_id='other'),
                   Entry('light.other_platform', 'eltako_gw1_00_00_00_02', platform='other'),
                   Entry('light.other_gateway', 'eltako_gw2_00_00_00_03')]
        registry = Registry(entries)
        self.assertEqual(migrate_entity_registry(registry, 'gateway-one', 1), 0)
        self.assertEqual(list(registry.entities.values()), entries)

    def test_conflict_aborts_before_any_updates(self):
        entries = [Entry('light.first', 'eltako_gw1_00_00_00_01'),
                   Entry('climate.old', 'eltako_gw1_00_00_00_47'),
                   Entry('climate.duplicate', 'eltako_gw_1_00_00_00_47')]
        registry = Registry(entries)
        with self.assertRaises(ConfigEntryError):
            migrate_entity_registry(registry, 'gateway-one', 1)
        self.assertEqual(list(registry.entities.values()), entries)

    def test_current_and_unknown_formats_are_untouched(self):
        for unique_id in ('eltako_gw_1_00_00_00_47', 'unrecognized', 'eltako_gw1_bad'):
            self.assertIsNone(replacement_unique_id(unique_id, 1))


class TestRealHomeAssistantRegistry(unittest.IsolatedAsyncioTestCase):
    async def test_same_registry_identity_is_reused_by_v2(self):
        from unittest.mock import patch
        from homeassistant.core import HomeAssistant
        from homeassistant.helpers.entity_registry import (
            EntityRegistry, EntityRegistryItems, RegistryEntryDisabler,
        )

        hass = HomeAssistant('/tmp/eltako-registry-unit-test')
        registry = EntityRegistry(hass)
        registry.entities = EntityRegistryItems()
        registry.deleted_entities = {}
        with patch.object(registry, 'async_schedule_save'):
            old = registry.async_get_or_create(
                'climate', 'eltako', 'eltako_gw1_00_00_00_47',
                suggested_object_id='living_room_heating', disabled_by=RegistryEntryDisabler.USER,
            )
            self.assertEqual(migrate_entity_registry(registry, None, 1), 1)
            new = registry.async_get_or_create('climate', 'eltako', 'eltako_gw_1_00_00_00_47')
            self.assertEqual(new.entity_id, 'climate.living_room_heating')
            self.assertEqual(new.id, old.id)
            self.assertEqual(new.disabled_by, RegistryEntryDisabler.USER)
            self.assertEqual(len(registry.entities), 1)
