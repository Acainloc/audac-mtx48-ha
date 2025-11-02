from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from .const import DOMAIN
from .hub import AudacHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = AudacHub(
        host=entry.data["host"],
        port=entry.data["port"],
        zones=entry.data["zones"],
        device_id=entry.data.get("device_id", "X001"),
        source_id=entry.data.get("source_id", "HA"),
    )
    await hub.async_connect()

    # Stocker un dict (pas un objet brut) évite certaines surprises côté options flow
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"hub": hub}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data and "hub" in data:
        await data["hub"].async_close()
    return unload_ok
