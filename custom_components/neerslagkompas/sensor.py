"""Forecast sensor and per-provider diagnostic sensors."""
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, SOURCE_INTERVALS
from .engine import assess
from .forecast_series import forecast_points


async def async_setup_entry(hass, entry, async_add_entities):
    coordinators = entry.runtime_data
    async_add_entities(
        [ForecastSensor(entry, coordinators)]
        + [
            SourceHealthSensor(entry, source, coordinators.get(source))
            for source in SOURCE_INTERVALS
        ]
    )


class BaseSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, entry, coordinator_map, suffix):
        self.entry, self.coordinators = entry, coordinator_map
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"NeerslagKompas {entry.title}",
            manufacturer="NeerslagKompas",
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        for coord in self.coordinators.values():
            self.async_on_remove(
                coord.async_add_listener(self.async_write_ha_state)
            )


class ForecastSensor(BaseSensor):
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, entry, coordinators):
        super().__init__(entry, coordinators, "forecast")
        self._attr_name = f"NeerslagKompas {entry.title} verwachting"

    def _assessment(self):
        return assess(
            {key: coord.current() for key, coord in self.coordinators.items()},
            datetime.now(timezone.utc),
        )

    @property
    def available(self):
        return bool(self._assessment().used_sources)

    @property
    def native_value(self):
        return self._assessment().state

    @property
    def extra_state_attributes(self):
        a = self._assessment()
        return {
            "next_rain_start": a.start.isoformat() if a.start else None,
            "max_intensity_mm_h": round(a.max_intensity_mm_h, 2)
            if a.max_intensity_mm_h is not None else None,
            "agreeing_sources": list(a.agreeing_sources),
            "used_sources": list(a.used_sources),
            "rain_within_30_minutes": a.rain_within_30m,
            "source_status": {
                name: (
                    "not_configured"
                    if name not in self.coordinators
                    else "available"
                    if self.coordinators[name].current()
                    else "unavailable"
                )
                for name in SOURCE_INTERVALS
            },
            "attribution": (
                "Buienradar.nl; Buienalarm/Infoplaza; "
                "KNMI Open Data; KNMI via Weerlive.nl"
            ),
        }


class SourceHealthSensor(BaseSensor):
    _attr_icon = "mdi:cloud-check-outline"

    def __init__(self, entry, source, coordinator):
        super().__init__(
            entry, {source: coordinator} if coordinator else {},
            f"source_{source}",
        )
        self.source, self.coord = source, coordinator
        self._attr_name = f"NeerslagKompas {entry.title} bron {source}"

    @property
    def native_value(self):
        if self.coord is None:
            return "Niet geconfigureerd"
        return "Beschikbaar" if self.coord.current() else "Niet beschikbaar"

    @property
    def extra_state_attributes(self):
        from . import current_location

        now = datetime.now(timezone.utc)
        data = self.coord.current() if self.coord else None
        latitude, longitude = current_location(self.hass, self.entry)
        series = forecast_points(data, now)
        return {
            "last_received": data.received_at.isoformat() if data else None,
            "attribution": data.attribution if data else None,
            "point_count": len(data.points) if data else 0,
            "forecast_points": series,
            "forecast_start": series[0]["datetime"] if series else None,
            "forecast_end": series[-1]["datetime"] if series else None,
            "latitude": round(latitude, 5),
            "longitude": round(longitude, 5),
            "spatial_resolution_km": 1 if self.source == "knmi_radar" and data else None,
        }
