from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_ZONES,
    DEFAULT_RATE_LIMIT_MS,
    DEFAULT_POLL_INTERVAL,
)

DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Optional("port", default=DEFAULT_PORT): int,
    vol.Optional("zones", default=DEFAULT_ZONES): vol.In([4, 8]),
    vol.Optional("device_id", default="M001"): str,
    vol.Optional("source_id", default="F001"): str,
})

class AudacConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"AUDAC MTX ({user_input['host']})", data=user_input)
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

    @callback
    def async_get_options_flow(self, config_entry):
        return AudacOptionsFlow(config_entry)

class AudacOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data_schema = vol.Schema({
            vol.Optional("poll_interval", default=self.entry.options.get("poll_interval", DEFAULT_POLL_INTERVAL)): int,
            vol.Optional("rate_limit_ms", default=self.entry.options.get("rate_limit_ms", DEFAULT_RATE_LIMIT_MS)): int,
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)
