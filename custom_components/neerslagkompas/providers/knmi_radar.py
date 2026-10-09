"""Official KNMI Data Platform radar_forecast/2.0 nowcast reader.

Validate KNMI HDF5 projection and calibration metadata before interpreting
point values. Unknown formats and missing measurements fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from io import BytesIO
from math import pi, sin, cos, tan, sqrt, radians, isfinite, floor
import re
from urllib.parse import quote

from ..models import RainPoint, SourceData

API = "https://api.dataplatform.knmi.nl/open-data/v1/datasets/radar_forecast/versions/2.0/files"
MAX_DOWNLOAD = 48 * 1024 * 1024


def check_http_status(response, stage: str) -> None:
    """Preserve HTTP status and safe stage only, never URLs or credentials."""
    from aiohttp import ClientResponseError
    try:
        response.raise_for_status()
    except ClientResponseError as error:
        error.neerslagkompas_stage = stage
        raise


@dataclass(frozen=True)
class Grid:
    """Validated KNMI v2 polar-stereographic metadata, in kilometres."""

    columns: int = 700
    rows: int = 765
    column_offset: float = 0.0
    row_offset: float = 3650.0
    pixel_x: float = 1.0
    pixel_y: float = -1.0
    major_radius: float = 6378.137
    minor_radius: float = 6356.752
    standard_latitude: float = 60.0


def _scalar(attrs, name):
    """Decode HDF5 single-value attributes (often one-element NumPy arrays)."""
    value = attrs[name]
    if hasattr(value, "shape") and value.shape == (1,):
        value = value[0]
    if isinstance(value, bytes):
        return value.decode("ascii")
    return value


def _grid_from_hdf5(file) -> Grid:
    geo = file["geographic"]
    projection = geo["map_projection"]
    if (
        _scalar(geo.attrs, "geo_pixel_def") != "LU"
        or _scalar(geo.attrs, "geo_par_pixel") != "X,Y"
        or _scalar(geo.attrs, "geo_dim_pixel") != "KM,KM"
        or _scalar(projection.attrs, "projection_name") != "STEREOGRAPHIC"
    ):
        raise ValueError("Unsupported KNMI radar grid convention")

    proj4 = str(_scalar(projection.attrs, "projection_proj4_params"))
    parts = dict(item[1:].split("=", 1) for item in proj4.split() if item.startswith("+") and "=" in item)
    if not (
        parts.get("proj") == "stere"
        and parts.get("units") == "km"
        and float(parts.get("lat_0", "nan")) == 90
        and float(parts.get("lon_0", "nan")) == 0
        and float(parts.get("x_0", "nan")) == 0
        and float(parts.get("y_0", "nan")) == 0
    ):
        raise ValueError("Unsupported KNMI radar projection")
    grid = Grid(
        columns=int(_scalar(geo.attrs, "geo_number_columns")),
        rows=int(_scalar(geo.attrs, "geo_number_rows")),
        column_offset=float(_scalar(geo.attrs, "geo_column_offset")),
        row_offset=float(_scalar(geo.attrs, "geo_row_offset")),
        pixel_x=float(_scalar(geo.attrs, "geo_pixel_size_x")),
        pixel_y=float(_scalar(geo.attrs, "geo_pixel_size_y")),
        major_radius=float(parts["a"]) / 1000,
        minor_radius=float(parts["b"]) / 1000,
        standard_latitude=float(parts["lat_ts"]),
    )
    if (
        grid.columns <= 0 or grid.rows <= 0 or grid.pixel_x <= 0
        or grid.pixel_y >= 0 or grid.major_radius <= grid.minor_radius
        or not all(isfinite(value) for value in (
            grid.column_offset, grid.row_offset, grid.pixel_x, grid.pixel_y,
            grid.major_radius, grid.minor_radius, grid.standard_latitude
        ))
    ):
        raise ValueError("Invalid KNMI radar grid geometry")
    return grid


def lonlat_to_pixel(latitude: float, longitude: float, grid: Grid | None = None) -> tuple[int, int]:
    """Select containing raster cell, not the nearest upper-left pixel corner."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid geographical coordinates")
    grid = grid or Grid()
    a, b = grid.major_radius, grid.minor_radius
    eccentricity = sqrt(1 - (b / a) ** 2)
    phi = radians(latitude)
    standard = radians(grid.standard_latitude)

    def t(angle):
        return tan(pi / 4 - angle / 2) / (
            (1 - eccentricity * sin(angle)) / (1 + eccentricity * sin(angle))
        ) ** (eccentricity / 2)

    m_standard = cos(standard) / sqrt(1 - eccentricity**2 * sin(standard)**2)
    rho = a * m_standard * t(phi) / t(standard)
    x = rho * sin(radians(longitude))
    y = -rho * cos(radians(longitude))
    # HDF5 geo_pixel_def=LU: offsets reference the upper-left raster corner.
    # The Y projection origin is -geo_row_offset, and pixel_y is negative.
    col = floor((x - grid.column_offset) / grid.pixel_x)
    row = floor((y + grid.row_offset) / grid.pixel_y)
    if not (0 <= row < grid.rows and 0 <= col < grid.columns):
        raise ValueError("Location outside KNMI radar forecast grid")
    return row, col


def parse_datetime(value) -> datetime:
    if isinstance(value, bytes):
        value = value.decode("ascii")
    return datetime.strptime(
        str(value), "%d-%b-%Y;%H:%M:%S.%f"
    ).replace(tzinfo=timezone.utc)


def _calibration(group) -> tuple[float, float, frozenset[int]]:
    cal = group["calibration"].attrs
    if _scalar(cal, "calibration_flag") != "Y":
        raise ValueError("KNMI radar image has no calibration")
    formula = str(_scalar(cal, "calibration_formulas")).replace(" ", "")
    match = re.fullmatch(r"GEO=([+-]?\d+(?:\.\d+)?)\*PV([+-]\d+(?:\.\d+)?)", formula)
    if not match:
        raise ValueError("Unsupported KNMI radar calibration formula")
    factor, offset = map(float, match.groups())
    if not all(isfinite(v) for v in (factor, offset)) or factor <= 0:
        raise ValueError("Invalid KNMI radar calibration")
    invalid = frozenset({
        int(_scalar(cal, "calibration_missing_data")),
        int(_scalar(cal, "calibration_out_of_image")),
    })
    return factor, offset, invalid


def parse_hdf5(
    blob: bytes, latitude: float, longitude: float, now: datetime
) -> SourceData:
    """Extract a verified point series off the Home Assistant event loop."""
    import h5py

    points = []
    with h5py.File(BytesIO(blob), "r") as file:
        grid = _grid_from_hdf5(file)
        row, col = lonlat_to_pixel(latitude, longitude, grid)
        count = int(_scalar(file["overview"].attrs, "number_image_groups"))
        if count != 25:
            raise ValueError("Unexpected KNMI nowcast image count")
        for index in range(1, count + 1):
            group = file[f"image{index}"]
            at = parse_datetime(group.attrs["image_datetime_valid"])
            raster = group["image_data"]
            if raster.ndim != 2 or raster.shape != (grid.rows, grid.columns):
                raise ValueError("Unsupported KNMI HDF5 image geometry")
            factor, offset, invalid = _calibration(group)
            raw = int(raster[row, col])
            if raw in invalid:
                # Missing is unknown; it must never be silently treated as dry.
                continue
            # The file calibration describes mm per five-minute image.
            value = (raw * factor + offset) * 12
            if not isfinite(value) or not (0 <= value <= 1000):
                raise ValueError("Invalid KNMI precipitation rate")
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
            check_http_status(response, "list_files")
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
            check_http_status(response, "get_download_url")
            payload = await response.json()
        signed_url = payload.get("temporaryDownloadUrl")
        if not signed_url or not signed_url.startswith("https://"):
            raise ValueError("KNMI did not provide a secure file URL")
        content = bytearray()
        async with self.session.get(signed_url, timeout=60) as response:
            check_http_status(response, "download_radar_file")
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
