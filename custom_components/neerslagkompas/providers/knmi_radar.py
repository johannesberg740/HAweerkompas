"""Official KNMI Data Platform radar_forecast/2.0 nowcast reader.

The KNMI HDF5 layout and projection are experimental pending real-file
validation on Home Assistant OS. No data is fabricated when extraction fails.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from io import BytesIO
from math import pi, sin, cos, tan, sqrt, radians, isfinite
from urllib.parse import quote

from ..models import RainPoint, SourceData

API = "https://api.dataplatform.knmi.nl/open-data/v1/datasets/radar_forecast/versions/2.0/files"
MAX_DOWNLOAD = 48 * 1024 * 1024
RADIUS_MAJOR_KM = 6378.14
RADIUS_MINOR_KM = 6356.75
GEO_ROW_OFFSET = 3649.98193359375


def lonlat_to_pixel(latitude: float, longitude: float) -> tuple[int, int]:
    """Polar stereographic projection, requires verification with live v2 data."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid geographical coordinates")
    a, b = RADIUS_MAJOR_KM, RADIUS_MINOR_KM
    eccentricity = sqrt(1 - (b / a) ** 2)
    phi = radians(latitude)
    standard = radians(60)

    def t(angle):
        return tan(pi / 4 - angle / 2) / (
            (1 - eccentricity * sin(angle)) / (1 + eccentricity * sin(angle))
        ) ** (eccentricity / 2)

    m_standard = cos(standard) / sqrt(1 - eccentricity**2 * sin(standard)**2)
    rho = a * m_standard * t(phi) / t(standard)
    x = rho * sin(radians(longitude))
    y = -rho * cos(radians(longitude))
    col, row = round(x), round(-GEO_ROW_OFFSET - y)
    if not (0 <= row < 765 and 0 <= col < 700):
        raise ValueError("Location outside KNMI radar forecast grid")
    return row, col


def parse_datetime(value) -> datetime:
    if isinstance(value, bytes):
        value = value.decode("ascii")
    return datetime.strptime(
        str(value), "%d-%b-%Y;%H:%M:%S.%f"
    ).replace(tzinfo=timezone.utc)


def parse_hdf5(
    blob: bytes, latitude: float, longitude: float, now: datetime
) -> SourceData:
    """Synchronous point extraction. Must run off Home Assistant event loop."""
    import h5py

    row, col = lonlat_to_pixel(latitude, longitude)
    points = []
    with h5py.File(BytesIO(blob), "r") as file:
        for index in range(1, 26):
            group = file[f"image{index}"]
            at = parse_datetime(group.attrs["image_datetime_valid"])
            raster = group["image_data"]
            if raster.ndim != 2 or raster.shape[0] <= row or raster.shape[1] <= col:
                raise ValueError("Unsupported KNMI HDF5 grid")
            raw = int(raster[row, col])
            if raw == 65535:
                continue
            # One raw count = 0.01 mm per five minutes.
            value = raw * 0.01 * 12
            if not isfinite(value) or value > 1000:
                continue
            points.append(RainPoint(at, value))
    if not points or abs(points[0].at - now) > timedelta(minutes=90):
        raise ValueError("Missing or stale KNMI nowcast")
    return SourceData(
        "knmi_radar", "nowcast", now, tuple(points),
        attribution="KNMI Open Data, radar_forecast/2.0 (CC BY 4.0)",
    )


class KnmiRadarClient:
    def __init__(self, session, api_key: str, executor):
        self.session, self.key, self.executor = session, api_key, executor
        self._last_filename = None
        self._last_coordinates = None
        self._last_data = None

    async def async_fetch(
        self, latitude: float, longitude: float, now: datetime
    ) -> SourceData:
        headers = {"Authorization": self.key}
        params = {"maxKeys": 1, "orderBy": "created", "sorting": "desc"}
        async with self.session.get(
            API, headers=headers, params=params, timeout=20
        ) as response:
            response.raise_for_status()
            file_list = await response.json()
        files = file_list.get("files") or []
        if not files or "filename" not in files[0]:
            raise ValueError("No KNMI radar files")
        filename = files[0]["filename"]
        if (
            self._last_filename == filename
            and self._last_coordinates == (latitude, longitude)
            and self._last_data is not None
        ):
            return self._last_data
        url = f"{API}/{quote(filename, safe='')}/url"
        async with self.session.get(
            url, headers=headers, timeout=20
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        signed_url = payload.get("temporaryDownloadUrl")
        if not signed_url or not signed_url.startswith("https://"):
            raise ValueError("KNMI did not provide a secure file URL")
        content = bytearray()
        async with self.session.get(signed_url, timeout=60) as response:
            response.raise_for_status()
            async for chunk in response.content.iter_chunked(256 * 1024):
                content.extend(chunk)
                if len(content) > MAX_DOWNLOAD:
                    raise ValueError("KNMI file exceeds download limit")
        result = await self.executor(
            parse_hdf5, bytes(content), latitude, longitude, now
        )
        self._last_filename = filename
        self._last_coordinates = (latitude, longitude)
        self._last_data = result
        return result
