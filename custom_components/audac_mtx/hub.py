from __future__ import annotations
import asyncio
import logging
import re
import time
from typing import Optional
from .const import TIMEOUT, RECV_EOL, SEND_EOL

_LOGGER = logging.getLogger(__name__)

class AudacProtocolError(Exception):
    pass

class AudacHub:
    def __init__(
        self,
        host: str,
        port: int,
        zones: int,
        device_id: str,
        source_id: str,
        rate_limit_ms: int = 120,
        poll_interval: int = 5,
    ):
        self.host = host
        self.port = port
        self.zones = zones
        self.device_id = device_id
        self.source_id = source_id
        self.rate_limit_ms = max(0, int(rate_limit_ms))
        self.poll_interval = max(1, int(poll_interval))
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._last_tx = 0.0

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
        # Frame: #|{dest}|{src}|{cmd}|{args...}|U|\r\n
        parts = ["#", self.device_id, self.source_id, command]
        parts += [f"{a}" for a in args]
        return "|".join(parts) + "|U|" + SEND_EOL

    async def _ensure_rate_limit(self):
        now = time.monotonic()
        delta = (self._last_tx + self.rate_limit_ms / 1000.0) - now
        if delta > 0:
            await asyncio.sleep(delta)

    async def _send_recv_once(self, payload: str) -> str:
        if not self._writer or not self._reader:
            await self.async_connect()
        async with self._lock:
            await self._ensure_rate_limit()
            _LOGGER.debug("TX: %s", payload.strip())
            self._writer.write(payload.encode())
            await self._writer.drain()
            self._last_tx = time.monotonic()
            data = await asyncio.wait_for(self._reader.readuntil(RECV_EOL), TIMEOUT)
            text = data.decode(errors="ignore").strip()
            _LOGGER.debug("RX: %s", text)
            return text

    async def _send_recv(self, payload: str) -> str:
        try:
            return await self._send_recv_once(payload)
        except Exception as exc:
            _LOGGER.warning("I/O error (%s). Reconnecting and retrying once...", exc)
            await self.async_close()
            await asyncio.sleep(0.2)
            await self.async_connect()
            return await self._send_recv_once(payload)

    # --- High level helpers ---
    async def set_volume(self, zone: int, value: int):
        value = max(0, min(100, int(value)))
        cmd = self._build(f"SV{zone:02d}", str(value))
        return await self._send_recv(cmd)

    async def set_mute(self, zone: int, muted: bool):
        cmd = self._build(f"SM{zone:02d}", "01" if muted else "00")
        return await self._send_recv(cmd)

    async def set_source(self, zone: int, source_index: int):
        # 1..8
        cmd = self._build(f"SR{zone:02d}", f"{source_index:02d}")
        return await self._send_recv(cmd)

    async def get_zone_info(self, zone: int) -> dict:
        cmd = self._build(f"GZI{zone:02d}")
        resp = await self._send_recv(cmd)
        return self._parse_gzi(resp)

    # --- Parsers ---
    def _parse_gzi(self, text: str) -> dict:
        """Best-effort parser for GZI response.
        Supports formats like:
        - #|M001|F001|GZI01|60|00|03|U|
        - #|M001|F001|GZI01|VOL|060|MUTE|00|SRC|03|U|
        Returns: {"volume": int(0..100), "mute": bool, "source": int(1..8)}
        """
        try:
            parts = text.strip("|\r\n").split("|")
            idx = next(i for i, p in enumerate(parts) if p.startswith("GZI"))
            tail = parts[idx + 1:]
        except Exception:
            tail = []

        volume = None
        mute = None
        source = None

        # Keyed form
        kv = {tail[i].upper(): tail[i + 1] for i in range(0, len(tail) - 1, 2) if tail[i].isalpha()}
        if kv:
            if "VOL" in kv or "VOLUME" in kv:
                m = re.search(r"\d+", kv.get("VOL", kv.get("VOLUME", "")))
                if m:
                    volume = int(m.group())
            if "MUTE" in kv:
                mute = kv["MUTE"].strip().upper() in ("1", "01", "ON", "TRUE")
            if "SRC" in kv or "SOURCE" in kv:
                m = re.search(r"\d+", kv.get("SRC", kv.get("SOURCE", "")))
                if m:
                    source = int(m.group())
        else:
            # Positional form: VOL|MUTE|SRC (numbers)
            nums = [int(n) for n in re.findall(r"\d+", "|".join(tail))]
            if len(nums) >= 1:
                volume = nums[0]
            if len(nums) >= 2:
                mute = nums[1] in (1,)
            if len(nums) >= 3:
                source = nums[2]

        # Clamp
        if volume is not None:
            volume = max(0, min(100, volume))
        if source is not None:
            source = max(1, min(8, source))
        if mute is None:
            mute = False

        return {"volume": volume, "mute": mute, "source": source}
