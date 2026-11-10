"""Fan attributes used by the Eltako standalone runtime."""

from enum import IntFlag

from ...helpers.entity import Entity


class FanEntityFeature(IntFlag):
    SET_SPEED = 1
    OSCILLATE = 2
    DIRECTION = 4
    PRESET_MODE = 8
    TURN_OFF = 16
    TURN_ON = 32


class FanEntity(Entity):
    @property
    def percentage(self):
        return getattr(self, "_attr_percentage", None)

    @property
    def is_on(self):
        return None if self.percentage is None else self.percentage > 0

    @property
    def state(self):
        if self.is_on is None:
            return None
        return "on" if self.is_on else "off"

    @property
    def state_attributes(self):
        return {"percentage": self.percentage} if self.percentage is not None else None
