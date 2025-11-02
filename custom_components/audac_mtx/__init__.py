from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from .const import DOMAIN, DEFAULT_RATE_LIMIT_MS, DEFAULT_POLL_INTERVAL
from .hub import AudacHub
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = AudacHub(
        host=entry.data["host"],
        port=entry.data["port"],
        zones=entry.data["zones"],
        device_id=entry.data.get("device_id", "M001"),
        source_id=entry.data.get("source_id", "F001"),
        rate_limit_ms=entry.options.get("rate_limit_ms", DEFAULT_RATE_LIMIT_MS),
        poll_interval=entry.options.get("poll_interval", DEFAULT_POLL_INTERVAL),
    )
    await hub.async_connect()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "presets": {},  # name -> {zone: {volume, mute, source}}
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_services(hass)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data[DOMAIN].pop(entry.entry_id)
    hub: AudacHub = data["hub"]
    await hub.async_close()
    await async_unregister_services(hass)
    return unload_ok
