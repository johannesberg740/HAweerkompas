"""Synthetic regression fixtures matching real KNMI radar_forecast/2.0 HDF5 metadata."""
from datetime import datetime, timezone, timedelta
from io import BytesIO

import h5py
import pytest

from custom_components.neerslagkompas.providers.knmi_radar import (
    lonlat_to_pixel, parse_hdf5,
)

NOW = datetime(2026, 10, 9, 17, 45, tzinfo=timezone.utc)


def _fixture(first=100, second=65534, third=65535, calibration="GEO=0.010000*PV+0.000000"):
    output = BytesIO()
    with h5py.File(output, "w") as f:
        geo = f.create_group("geographic")
        geo.attrs.update({
            "geo_column_offset": [0.0], "geo_row_offset": [3650.0],
            "geo_pixel_size_x": [1.0], "geo_pixel_size_y": [-1.0],
            "geo_number_columns": [700], "geo_number_rows": [765],
            "geo_pixel_def": "LU", "geo_par_pixel": "X,Y", "geo_dim_pixel": "KM,KM",
        })
        projection = geo.create_group("map_projection")
        projection.attrs.update({
            "projection_name": "STEREOGRAPHIC",
            "projection_proj4_params": (
                "+proj=stere +lat_0=90 +lon_0=0 +lat_ts=60 "
                "+a=6378137 +b=6356752 +x_0=0 +y_0=0 +units=km"
            ),
        })
        overview = f.create_group("overview")
        overview.attrs["number_image_groups"] = [25]
        row, col = lonlat_to_pixel(52.71, 5.75)
        for index in range(1, 26):
            group = f.create_group(f"image{index}")
            at = NOW + timedelta(minutes=(index - 1) * 5)
            group.attrs["image_datetime_valid"] = at.strftime("%d-%b-%Y;%H:%M:%S.000")
            raster = group.create_dataset("image_data", (765, 700), dtype="u2", fillvalue=0)
            raster[row, col] = {1: first, 2: second, 3: third}.get(index, 0)
            cal = group.create_group("calibration")
            cal.attrs.update({
                "calibration_flag": "Y",
                "calibration_formulas": calibration,
                "calibration_missing_data": [65534],
                "calibration_out_of_image": [65535],
            })
    return output.getvalue()


def test_emmeloord_containing_grid_cell():
    # Real KNMI v2 map metadata: upper-left pixel corner, 1 km pixels.
    assert lonlat_to_pixel(52.71, 5.75) == (353, 403)


def test_parse_calibration_and_skip_both_missing_codes():
    source = parse_hdf5(_fixture(), 52.71, 5.75, NOW)
    assert len(source.points) == 23
    assert source.points[0].intensity_mm_h == pytest.approx(12)
    assert source.points[1].at == NOW + timedelta(minutes=15)
    assert source.points[1].intensity_mm_h == 0


def test_missing_only_is_unavailable_not_dry():
    with pytest.raises(ValueError, match="Missing or stale"):
        parse_hdf5(_fixture(first=65534, second=65534, third=65535), 52.71, 5.75, NOW)


def test_reject_unknown_calibration():
    with pytest.raises(ValueError, match="Unsupported KNMI radar calibration"):
        parse_hdf5(_fixture(calibration="GEO=unknown"), 52.71, 5.75, NOW)


def test_reject_stale_file():
    with pytest.raises(ValueError, match="Missing or stale"):
        parse_hdf5(_fixture(), 52.71, 5.75, NOW + timedelta(hours=4))
