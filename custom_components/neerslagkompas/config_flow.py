"""GUI configuration. API keys stay in Home Assistant config entries."""
from __future__ import annotations

from uuid import uuid4
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers import selector
from .const import (
    DOMAIN, CONF_TRACK_HOME, CONF_KNMI_KEY, CONF_WEERLIVE_KEY,
    CONF_BUIENALARM, CONF_BUIENRADAR,
)


def form_schema(current=None):
    values = current or {}
    password = selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    )
    return vol.Schema({
        vol.Required(CONF_NAME, default=values.get(CONF_NAME, "Thuis")): str,
        vol.Required(CONF_TRACK_HOME, default=values.get(CONF_TRACK_HOME, True)): bool,
        vol.Optional(CONF_LATITUDE, default=values.get(CONF_LATITUDE, 52.0)): vol.Coerce(float),
        vol.Optional(CONF_LONGITUDE, default=values.get(CONF_LONGITUDE, 5.0)): vol.Coerce(float),
        vol.Required(CONF_BUIENRADAR, default=values.get(CONF_BUIENRADAR, True)): bool,
        vol.Required(CONF_BUIENALARM, default=values.get(CONF_BUIENALARM, True)): bool,
        vol.Optional(CONF_KNMI_KEY): password,
        vol.Optional(CONF_WEERLIVE_KEY): password,
    })


def valid_location(values):
    if values.get(CONF_TRACK_HOME, True):
        return True
    return (
        -90 <= values.get(CONF_LATITUDE, 999) <= 90
        and -180 <= values.get(CONF_LONGITUDE, 999) <= 180
    )


class NeerslagKompasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if not valid_location(user_input):
                return self.async_show_form(
                    step_id="user",
                    data_schema=form_schema(user_input),
                    errors={"base": "invalid_location"},
                )
            if user_input.get(CONF_TRACK_HOME, True) and any(
                entry.data.get(CONF_TRACK_HOME, True)
                for entry in self._async_current_entries()
            ):
                return self.async_abort(reason="home_already_configured")
            await self.async_set_unique_id(uuid4().hex)
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Thuis"), data=user_input
            )
        return self.async_show_form(step_id="user", data_schema=form_schema())

    @staticmethod
    def async_get_options_flow(config_entry):
        return NeerslagKompasOptionsFlow()


class NeerslagKompasOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        existing = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            if not valid_location(user_input):
                return self.async_show_form(
                    step_id="init",
                    data_schema=form_schema(user_input),
                    errors={"base": "invalid_location"},
                )
            for key in (CONF_KNMI_KEY, CONF_WEERLIVE_KEY):
                if not user_input.get(key):
                    user_input.pop(key, None)
                    if existing.get(key):
                        user_input[key] = existing[key]
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=form_schema(existing)
        )
