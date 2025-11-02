from __future__ import annotations
import asyncio
import logging
from typing import Optional
from .const import TIMEOUT, RECV_EOL, SEND_EOL

_LOGGER = logging.getLogger(__name__)

class AudacProtocolError(Exception):
    pass

class AudacHub:
    def __init__(self, host: str, port: int, zones: int, device_id: str, source_id: str):
        self.host = host
        self.port = port
        self.zones = zones
        self.device_id = device_id   # ex: X001
        self.source_id = source_id   # ex: HA
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()

    async def async_connect(self):
        _LOGGER.info("Connecting to AUDAC MTX at %s:%s", self.host, self.port)
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), TIMEOUT
        )

    async def async_close(self):
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as exc:
                _LOGGER.debug("Close error: %s", exc)
        self._reader = self._writer = None

    def _build(self, command: str, *args: str) -> str:
        # #|{dest}|{src}|{cmd}|{args...}|U|<CR><LF>
        parts = ["#", self.device_id, self.source_id, command]
        parts += [f"{a}" for a in args]
        return "|".join(parts) + "|U|" + SEND_EOL

    async def _send_recv(self, payload: str) -> str:
        if not self._writer or not self._reader:
            await self.async_connect()
        async with self._lock:
            _LOGGER.debug("TX: %s", payload.strip())
            self._writer.write(payload.encode())
            await self._writer.drain()
            data = await asyncio.wait_for(self._reader.readuntil(RECV_EOL), TIMEOUT)
            text = data.decode(errors="ignore").strip()
            _LOGGER.debug("RX: %s", text)
            return text

    # --- Helpers haut-niveau (formats conformes MTX) ---
    async def set_volume(self, zone: int, percent_value: int):
        """
        Volume UI en pourcentage (0..100) -> protocole AUDAC 0..70 (dB step).
        0 = max (sur certaines séries), mais on suit la doc qui accepte 0..70.
        """
        p = max(0, min(100, int(percent_value)))
        db = round(p * 70 / 100)  # mapping simple 0..100% -> 0..70
        # Protocole : SVx  (x = 1..8, SANS zéro)
        cmd = self._build(f"SV{zone}", str(db))
        return await self._send_recv(cmd)

    async def set_mute(self, zone: int, muted: bool):
        # Protocole : SM0x (AVEC zéro) ; arg 0/1
        cmd = self._build(f"SM{zone:02d}", "1" if muted else "0")
        return await self._send_recv(cmd)

    async def set_source(self, zone: int, source_index: int):
        # Protocole : SRx (SANS zéro), arg 0..8 (0 = none)
        idx = max(0, min(8, int(source_index)))
        cmd = self._build(f"SR{zone}", str(idx))
        return await self._send_recv(cmd)

    async def get_zone_info(self, zone: int):
        # Protocole : GZI0x (AVEC zéro), arg "0"
        cmd = self._build(f"GZI{zone:02d}", "0")
        return await self._send_recv(cmd)
