"""Independent provider polling and health status."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .models import SourceData, is_fresh

_LOGGER = logging.getLogger(__name__)


class SourceCoordinator(DataUpdateCoordinator[SourceData]):
    def __init__(self, hass, entry, source: str, client, location, interval):
        super().__init__(
            hass, _LOGGER, config_entry=entry,
            name=f"neerslagkompas_{source}_{entry.entry_id}",
            update_interval=interval,
        )
        self.source, self.client, self.location = source, client, location

    async def _async_update_data(self) -> SourceData:
        try:
            lat, lon = self.location()
            return await self.client.async_fetch(
                lat, lon, datetime.now(timezone.utc)
            )
        except Exception as error:
            # Do not print API error strings; these may contain credentials.
            _LOGGER.warning(
                "NeerslagKompas provider %s failed (%s)",
                self.source, type(error).__name__,
            )
            raise UpdateFailed(f"{self.source} unavailable") from None

    def current(self) -> SourceData | None:
        if self.last_update_success and is_fresh(
            self.data, datetime.now(timezone.utc)
        ):
            return self.data
        return None
