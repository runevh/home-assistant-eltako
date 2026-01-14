"""Support for selecting climate controller priority."""
from __future__ import annotations

from eltakobus.util import AddressExpression
from eltakobus.eep import *

from homeassistant.components.select import SelectEntity
from homeassistant import config_entries
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from . import config_helpers, get_gateway_from_hass, get_device_config_for_gateway
from .config_helpers import DeviceConf
from .device import *
from .gateway import EnOceanGateway
from .const import *


def _get_controller_priority_enum():
    return getattr(A5_10_06, "ControllerPriority", getattr(A5_10_06, "Controller_Priority", None))


def _priority_to_option(priority) -> str | None:
    if priority is None:
        return None
    desc = getattr(priority, "description", None) or getattr(priority, "label", None)
    if desc:
        return desc
    value = getattr(priority, "value", priority)
    if isinstance(value, tuple) and len(value) > 0 and isinstance(value[-1], str):
        return value[-1]
    return getattr(priority, "name", None) or str(value)


def _priority_from_option(option: str):
    enum = _get_controller_priority_enum()
    if enum is None or option is None:
        return None

    if hasattr(enum, "find_by_description"):
        try:
            found = enum.find_by_description(option)
            if found is not None:
                return found
        except Exception:
            pass

    for prio in enum:
        if option == _priority_to_option(prio) or option == getattr(prio, "name", None) or option == str(getattr(prio, "value", None)):
            return prio

    return None


def _priority_options():
    enum = _get_controller_priority_enum()
    if enum is None:
        return []
    return [_priority_to_option(p) for p in enum]


def _default_priority_option():
    enum = _get_controller_priority_enum()
    if enum is None:
        return None
    if hasattr(enum, "AUTO"):
        return _priority_to_option(getattr(enum, "AUTO"))
    options = _priority_options()
    if options:
        return options[0]
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eltako select platform."""
    gateway: EnOceanGateway = get_gateway_from_hass(hass, config_entry)
    config: ConfigType = get_device_config_for_gateway(hass, config_entry, gateway)

    entities: list[EltakoEntity] = []

    platform = Platform.CLIMATE
    if platform in config:
        for entity_config in config[platform]:
            try:
                dev_config = None
                dev_config = DeviceConf(entity_config)
                if len(_priority_options()) == 0:
                    LOGGER.warning("[%s %s] Controller priorities not supported by library, skip creating select.", platform, dev_config.id)
                    continue
                entities.append(ClimatePriority(platform, gateway, dev_config.id, dev_config.name, dev_config.eep))

            except Exception as e:
                dev_id = getattr(dev_config, "id", None)
                LOGGER.warning("[%s %s] Could not load configuration", platform, str(dev_id))
                LOGGER.critical(e, exc_info=True)

    validate_actuators_dev_and_sender_id(entities)
    log_entities_to_be_added(entities, platform)
    async_add_entities(entities)


class ClimatePriority(EltakoEntity, SelectEntity, RestoreEntity):
    """Select controller priority for a climate actuator."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP):
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep)

        self.name = "Priority"
        self.event_id = config_helpers.get_bus_event_type(gateway.base_id, EVENT_CLIMATE_PRIORITY_SELECTED, self.dev_id)

        self._attr_options = _priority_options()
        self._attr_current_option = _default_priority_option()
        if self._attr_current_option is None and len(self._attr_options) > 0:
            self._attr_current_option = self._attr_options[0]

    def load_value_initially(self, latest_state:State):
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] latest state - state: {latest_state.state}")
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] latest state - attributes: {latest_state.attributes}")
        try:
            self._attr_current_option = latest_state.state
            if self._attr_current_option in [None, 'unknown']:
                self._attr_current_option = _default_priority_option()

        except Exception as e:
            self._attr_current_option = _default_priority_option()
            raise e

        # send value to initially set value of climate controller
        self.hass.bus.fire(self.event_id, { "priority": self._attr_current_option })

        self.schedule_update_ha_state()

        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] value initially loaded: [state: {self.state}]")


    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""

        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] selected option: {option}")
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] Send event id: '{self.event_id}' data: '{option}'")

        self.hass.bus.fire(self.event_id, { "priority": option })

        self._attr_current_option = option
        self.schedule_update_ha_state()
