"""Rain expected within thirty minutes (forecast, not observation)."""
from datetime import datetime, timezone

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .engine import assess


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RainSoonSensor(entry)])


class RainSoonSensor(BinarySensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, entry):
        self.entry = entry
        self.coordinators = entry.runtime_data
        self._attr_name = f"NeerslagKompas {entry.title} regen binnen 30 minuten"
        self._attr_unique_id = f"{entry.entry_id}_rain_30m"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        for coord in self.coordinators.values():
            self.async_on_remove(
                coord.async_add_listener(self.async_write_ha_state)
            )

    def _assessment(self):
        return assess(
            {s: c.current() for s, c in self.coordinators.items()},
            datetime.now(timezone.utc),
        )

    @property
    def available(self):
        return self._assessment().rain_within_30m is not None

    @property
    def is_on(self):
        return self._assessment().rain_within_30m
