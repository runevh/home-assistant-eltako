"""The v2 platform modules must load without a real Home Assistant install."""

import importlib

import pytest
import voluptuous as vol


def test_cover_and_fan_platforms_import():
    for name in ('cover', 'fan'):
        module = importlib.import_module(f'custom_components.eltako.{name}')
        assert callable(module.async_setup_entry)


def test_cover_state_and_position_attributes():
    from homeassistant.components.cover import CoverEntity

    cover = CoverEntity()
    assert cover.state is None
    cover._attr_is_closed = False
    cover._attr_current_cover_position = 40
    cover._attr_current_cover_tilt_position = 60
    assert cover.state == 'open'
    assert cover.state_attributes == {'current_position': 40, 'current_tilt_position': 60}
    cover._attr_is_closing = True
    assert cover.state == 'closing'


def test_fan_state_tracks_percentage():
    from homeassistant.components.fan import FanEntity

    fan = FanEntity()
    assert fan.state is None
    fan._attr_percentage = 75
    assert fan.state == 'on'
    assert fan.state_attributes == {'percentage': 75}
    fan._attr_percentage = 0
    assert fan.state == 'off'


def test_cover_service_entity_ids():
    from homeassistant.helpers.config_validation import entity_ids

    assert entity_ids('cover.one, cover.two') == ['cover.one', 'cover.two']
    assert entity_ids(['cover.one']) == ['cover.one']
    with pytest.raises(vol.Invalid):
        entity_ids(['not an entity'])


def test_legacy_entity_migration_in_standalone():
    from types import SimpleNamespace
    from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
    from homeassistant.helpers.entity_registry import EntityRegistry
    from custom_components.eltako.core.entity_migration import migrate_entity_registry

    assert issubclass(ConfigEntryError, HomeAssistantError)
    registry = EntityRegistry(SimpleNamespace(data={}))
    entry = registry.async_get_or_create(
        entity_id='climate.bedroom', unique_id='eltako_gw1_00_00_00_4a',
        platform='eltako', domain='climate', config_entry_id='gateway-1',
    )
    entry.disabled_by = 'user'
    assert migrate_entity_registry(registry, 'gateway-1', 1) == 1
    assert registry.async_get('climate.bedroom') is entry
    assert entry.unique_id == 'eltako_gw_1_00_00_00_4a'
    assert entry.disabled_by == 'user'
    assert migrate_entity_registry(registry, 'gateway-1', 1) == 0
