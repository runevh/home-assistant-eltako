"""Cover types used by the integration's schema and standalone entities."""

from enum import IntFlag, StrEnum

import voluptuous as vol

from ...helpers.entity import Entity

ATTR_POSITION = "position"
ATTR_TILT_POSITION = "tilt_position"


class CoverDeviceClass(StrEnum):
    AWNING = "awning"
    BLIND = "blind"
    CURTAIN = "curtain"
    DAMPER = "damper"
    DOOR = "door"
    GARAGE = "garage"
    GATE = "gate"
    SHADE = "shade"
    SHUTTER = "shutter"
    WINDOW = "window"


DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.Coerce(CoverDeviceClass))


class CoverState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"


class CoverEntityFeature(IntFlag):
    OPEN = 1
    CLOSE = 2
    SET_POSITION = 4
    STOP = 8
    OPEN_TILT = 16
    CLOSE_TILT = 32
    STOP_TILT = 64
    SET_TILT_POSITION = 128


class CoverEntity(Entity):
    @property
    def is_closed(self):
        return getattr(self, "_attr_is_closed", None)

    @property
    def is_opening(self):
        return getattr(self, "_attr_is_opening", False)

    @property
    def is_closing(self):
        return getattr(self, "_attr_is_closing", False)

    @property
    def current_cover_position(self):
        return getattr(self, "_attr_current_cover_position", None)

    @property
    def current_cover_tilt_position(self):
        return getattr(self, "_attr_current_cover_tilt_position", None)

    @property
    def state(self):
        if self.is_opening:
            return CoverState.OPENING
        if self.is_closing:
            return CoverState.CLOSING
        if self.is_closed is None:
            return None
        return CoverState.CLOSED if self.is_closed else CoverState.OPEN

    @property
    def state_attributes(self):
        return {key: value for key, value in (
            ("current_position", self.current_cover_position),
            ("current_tilt_position", self.current_cover_tilt_position),
        ) if value is not None}
