from __future__ import annotations
from typing import Any, Dict
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN

SERVICE_SAVE = "save_preset"
SERVICE_LOAD = "load_preset"

async def async_register_services(hass: HomeAssistant):
    async def handle_save(call: ServiceCall):
        name: str = call.data["name"]
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        hub = data["hub"]
        # Query actual state from device to be accurate
        zones_snapshot: Dict[int, Dict[str, Any]] = {}
        for zone in range(1, hub.zones + 1):
            info = await hub.get_zone_info(zone)
            zones_snapshot[zone] = info
        data["presets"][name] = zones_snapshot

    async def handle_load(call: ServiceCall):
        name: str = call.data["name"]
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        hub = data["hub"]
        preset = data["presets"].get(name, {})
        for zone, z in preset.items():
            if z.get("volume") is not None:
                await hub.set_volume(zone, int(z["volume"]))
            if z.get("mute") is not None:
                await hub.set_mute(zone, bool(z["mute"]))
            if z.get("source") is not None:
                await hub.set_source(zone, int(z["source"]))

    hass.services.async_register(DOMAIN, SERVICE_SAVE, handle_save)
    hass.services.async_register(DOMAIN, SERVICE_LOAD, handle_load)

async def async_unregister_services(hass: HomeAssistant):
    try:
        hass.services.async_remove(DOMAIN, SERVICE_SAVE)
        hass.services.async_remove(DOMAIN, SERVICE_LOAD)
    except Exception:
        pass
