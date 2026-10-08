"""Standalone precipitation integration."""
from __future__ import annotations

import asyncio

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, EVENT_CORE_CONFIG_UPDATE, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (DOMAIN, CONF_TRACK_HOME, CONF_KNMI_KEY, CONF_WEERLIVE_KEY,
                    CONF_BUIENALARM, CONF_BUIENRADAR, SOURCE_INTERVALS)
from .coordinator import SourceCoordinator
from .providers.buienradar import BuienradarClient
from .providers.buienalarm import BuienalarmClient
from .providers.knmi_radar import KnmiRadarClient
from .providers.weerlive import WeerliveClient

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


def current_location(hass, entry):
    settings = {**entry.data, **entry.options}
    if settings.get(CONF_TRACK_HOME, True):
        return hass.config.latitude, hass.config.longitude
    return float(settings[CONF_LATITUDE]), float(settings[CONF_LONGITUDE])


async def async_setup_entry(hass, entry) -> bool:
    settings = {**entry.data, **entry.options}
    session = async_get_clientsession(hass)
    providers = {}

    if settings.get(CONF_BUIENRADAR, True):
        providers["buienradar"] = BuienradarClient(session)
    if settings.get(CONF_BUIENALARM, True):
        providers["buienalarm"] = BuienalarmClient(session)
    if settings.get(CONF_KNMI_KEY):
        providers["knmi_radar"] = KnmiRadarClient(
            session, settings[CONF_KNMI_KEY], hass.async_add_executor_job
        )
    if settings.get(CONF_WEERLIVE_KEY):
        providers["weerlive"] = WeerliveClient(session, settings[CONF_WEERLIVE_KEY])

    location = lambda: current_location(hass, entry)
    coordinators = {
        source: SourceCoordinator(
            hass, entry, source, client, location, SOURCE_INTERVALS[source]
        )
        for source, client in providers.items()
    }
    entry.runtime_data = coordinators

    # Provider failures are isolated; missing sources never become "dry".
    await asyncio.gather(
        *(coordinator.async_refresh() for coordinator in coordinators.values())
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if settings.get(CONF_TRACK_HOME, True):
        async def refresh_location(event):
            await asyncio.gather(
                *(coordinator.async_request_refresh() for coordinator in coordinators.values())
            )
        entry.async_on_unload(hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, refresh_location))

    entry.async_on_unload(entry.add_update_listener(_on_options_update))
    return True


async def _on_options_update(hass, entry):
    name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, entry.title))
    if name != entry.title:
        hass.config_entries.async_update_entry(entry, title=name)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    success = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if success:
        entry.async_unload()
    return success
