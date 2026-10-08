"""Independent provider polling and health status."""
from __future__ import annotations

import logging

from aiohttp import ClientResponseError
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
        self.last_error = None

    async def _async_update_data(self) -> SourceData:
        try:
            lat, lon = self.location()
            data = await self.client.async_fetch(
                lat, lon, datetime.now(timezone.utc)
            )
            self.last_error = None
            return data
        except Exception as error:
            # Do not log exception text: response URLs may contain secrets.
            if isinstance(error, ClientResponseError):
                stage = getattr(error, "neerslagkompas_stage", "http_request")
                detail = f"HTTP {error.status}, stage {stage}"
            else:
                detail = type(error).__name__
            self.last_error = detail
            _LOGGER.warning(
                "NeerslagKompas provider %s failed: %s", self.source, detail
            )
            raise UpdateFailed(f"{self.source} unavailable: {detail}") from None

    def current(self) -> SourceData | None:
        if self.last_update_success and is_fresh(
            self.data, datetime.now(timezone.utc)
        ):
            return self.data
        return None
