"""
Support for KNX/IP covers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/cover.knx/
"""
import asyncio
import voluptuous as vol

from custom_components.xknx import DATA_XKNX, ATTR_DISCOVER_DEVICES
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.components.cover import (
    CoverDevice, PLATFORM_SCHEMA, SUPPORT_OPEN, SUPPORT_CLOSE,
    SUPPORT_SET_POSITION, SUPPORT_STOP, SUPPORT_SET_TILT_POSITION,
    ATTR_POSITION, ATTR_TILT_POSITION)
from homeassistant.core import callback
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

CONF_MOVE_LONG_ADDRESS = 'move_long_address'
CONF_MOVE_SHORT_ADDRESS = 'move_short_address'
CONF_POSITION_ADDRESS = 'position_address'
CONF_POSITION_STATE_ADDRESS = 'position_state_address'
CONF_ANGLE_ADDRESS = 'angle_address'
CONF_ANGLE_STATE_ADDRESS = 'angle_state_address'
CONF_TRAVELLING_TIME_DOWN = 'travelling_time_down'
CONF_TRAVELLING_TIME_UP = 'travelling_time_up'
CONF_INVERT_POSITION = 'invert_position'
CONF_INVERT_ANGLE = 'invert_angle'

DEFAULT_TRAVEL_TIME = 25
DEFAULT_NAME = 'XKNX Cover'
DEPENDENCIES = ['xknx']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MOVE_LONG_ADDRESS): cv.string,
    vol.Optional(CONF_MOVE_SHORT_ADDRESS): cv.string,
    vol.Optional(CONF_POSITION_ADDRESS): cv.string,
    vol.Optional(CONF_POSITION_STATE_ADDRESS): cv.string,
    vol.Optional(CONF_ANGLE_ADDRESS): cv.string,
    vol.Optional(CONF_ANGLE_STATE_ADDRESS): cv.string,
    vol.Optional(CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME):
        cv.positive_int,
    vol.Optional(CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME):
        cv.positive_int,
    vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
    vol.Optional(CONF_INVERT_ANGLE, default=False): cv.boolean,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices,
                         discovery_info=None):
    """Set up cover(s) for KNX platform."""
    if DATA_XKNX not in hass.data \
            or not hass.data[DATA_XKNX].initialized:
        return False

    if discovery_info is not None:
        async_add_devices_discovery(hass, discovery_info, async_add_devices)
    else:
        async_add_devices_config(hass, config, async_add_devices)

    return True


@callback
def async_add_devices_discovery(hass, discovery_info, async_add_devices):
    """Set up covers for KNX platform configured via xknx.yaml."""
    entities = []
    for device_name in discovery_info[ATTR_DISCOVER_DEVICES]:
        device = hass.data[DATA_XKNX].xknx.devices[device_name]
        entities.append(KNXCover(hass, device))
    async_add_devices(entities)


@callback
def async_add_devices_config(hass, config, async_add_devices):
    """Set up cover for KNX platform configured within plattform."""
    import xknx
    cover = xknx.devices.Cover(
        hass.data[DATA_XKNX].xknx,
        name=config.get(CONF_NAME),
        group_address_long=config.get(CONF_MOVE_LONG_ADDRESS),
        group_address_short=config.get(CONF_MOVE_SHORT_ADDRESS),
        group_address_position_state=config.get(
            CONF_POSITION_STATE_ADDRESS),
        group_address_angle=config.get(CONF_ANGLE_ADDRESS),
        group_address_angle_state=config.get(CONF_ANGLE_STATE_ADDRESS),
        group_address_position=config.get(CONF_POSITION_ADDRESS),
        travel_time_down=config.get(CONF_TRAVELLING_TIME_DOWN),
        travel_time_up=config.get(CONF_TRAVELLING_TIME_UP),
        invert_position=config.get(CONF_INVERT_POSITION),
        invert_angle=config.get(CONF_INVERT_ANGLE))

    hass.data[DATA_XKNX].xknx.devices.add(cover)
    async_add_devices([KNXCover(hass, cover)])


class KNXCover(CoverDevice):
    """Representation of a KNX cover."""

    def __init__(self, hass, device):
        """Initialize the cover."""
        self.device = device
        self.hass = hass
        self.async_register_callbacks()

        self._unsubscribe_auto_updater = None

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""
        @asyncio.coroutine
        def after_update_callback(device):
            """Callback after device was updated."""
            # pylint: disable=unused-argument
            yield from self.async_update_ha_state()
        self.device.register_device_updated_cb(after_update_callback)

    @property
    def name(self):
        """Return the name of the KNX device."""
        return self.device.name

    @property
    def should_poll(self):
        """No polling needed within KNX."""
        return False

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | \
            SUPPORT_SET_POSITION | SUPPORT_STOP
        if self.device.supports_angle:
            supported_features |= SUPPORT_SET_TILT_POSITION
        return supported_features

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self.device.current_position()

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.device.is_closed()

    @asyncio.coroutine
    def async_close_cover(self, **kwargs):
        """Close the cover."""
        if not self.device.is_closed():
            yield from self.device.set_down()
            self.start_auto_updater()

    @asyncio.coroutine
    def async_open_cover(self, **kwargs):
        """Open the cover."""
        if not self.device.is_open():
            yield from self.device.set_up()
            self.start_auto_updater()

    @asyncio.coroutine
    def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            yield from self.device.set_position(position)
            self.start_auto_updater()

    @asyncio.coroutine
    def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        yield from self.device.stop()
        self.stop_auto_updater()

    @property
    def current_cover_tilt_position(self):
        """Return current tilt position of cover."""
        if not self.device.supports_angle:
            return None
        return self.device.current_angle()

    @asyncio.coroutine
    def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        if ATTR_TILT_POSITION in kwargs:
            tilt_position = kwargs[ATTR_TILT_POSITION]
            yield from self.device.set_angle(tilt_position)

    def start_auto_updater(self):
        """Start the autoupdater to update HASS while cover is moving."""
        if self._unsubscribe_auto_updater is None:
            self._unsubscribe_auto_updater = async_track_utc_time_change(
                self.hass, self.auto_updater_hook)

    def stop_auto_updater(self):
        """Stop the autoupdater."""
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()
            self._unsubscribe_auto_updater = None

    @callback
    def auto_updater_hook(self, now):
        """Callback for autoupdater."""
        # pylint: disable=unused-argument
        self.async_schedule_update_ha_state()
        if self.device.position_reached():
            self.stop_auto_updater()

        self.hass.add_job(self.device.auto_stop_if_necessary())
