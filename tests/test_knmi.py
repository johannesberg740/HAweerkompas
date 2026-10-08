from datetime import datetime, timezone, timedelta
from io import BytesIO
from custom_components.neerslagkompas.providers.knmi_radar import (
    lonlat_to_pixel, parse_hdf5,
)

UTC = timezone.utc


def test_projection_grid_origin():
    row, col = lonlat_to_pixel(55.973602294921875, 0)
    assert (row, col) == (0, 0)


def test_hdf5_point_and_units():
    import h5py
    now = datetime(2026, 10, 8, 13, 15, tzinfo=UTC)
    lat, lon = 52.71, 5.73
    row, col = lonlat_to_pixel(lat, lon)
    output = BytesIO()
    with h5py.File(output, "w") as h5:
        for i in range(1, 26):
            group = h5.create_group(f"image{i}")
            at = now + timedelta(minutes=(i - 1) * 5)
            group.attrs["image_datetime_valid"] = at.strftime(
                "%d-%b-%Y;%H:%M:%S.000"
            )
            data = group.create_dataset(
                "image_data", shape=(765, 700),
                dtype="u2", chunks=(1, 700), fillvalue=0
            )
            data[row, col] = 10 if i == 1 else 0
    forecast = parse_hdf5(output.getvalue(), lat, lon, now)
    assert len(forecast.points) == 25
    assert abs(forecast.points[0].intensity_mm_h - 1.2) < 1e-9
    assert forecast.points[1].intensity_mm_h == 0

def test_http_error_stage_is_available_without_url_logging():
    from aiohttp import ClientResponseError
    from custom_components.neerslagkompas.providers.knmi_radar import check_http_status

    class FakeResponse:
        def raise_for_status(self):
            raise ClientResponseError(
                request_info=None, history=(), status=403,
                message="Do not expose endpoint details"
            )

    try:
        check_http_status(FakeResponse(), "list_files")
    except ClientResponseError as error:
        assert error.status == 403
        assert error.neerslagkompas_stage == "list_files"
    else:
        raise AssertionError("Expected HTTP error")
