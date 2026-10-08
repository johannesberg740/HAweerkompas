# Weerlive test fixture provenance

`weerlive-amsterdam-v2.json` is a reduced version of the response sample in
[golles/python-weerlive v0.2.4](https://github.com/golles/python-weerlive/blob/v0.2.4/tests/fixtures/amsterdam.json).

Original fixture copyright 2024-2026 golles, published under the MIT License:
https://github.com/golles/python-weerlive/blob/v0.2.4/LICENSE

Data is illustrative historical provider output, not current weather data.
Contains one daily and two hourly forecasts. All required real-schema
response fields are retained so upstream `Response.from_json` validates it.
