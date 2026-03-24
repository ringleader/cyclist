"""Storage layer for Cyclist."""
from __future__ import annotations

import logging
from typing import Any, TypedDict, cast
from datetime import date

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, DOMAIN

_LOGGER = logging.getLogger(__name__)

class CyclistSettings(TypedDict):
    cycle_length: int
    period_duration: int

class CyclistStorageData(TypedDict):
    version: int
    last_period_start: str | None
    settings: CyclistSettings

class CyclistData:
    """Manages Cyclist data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: CyclistStorageData | None = None
        self._listeners: list[callable] = []

    async def async_load(self) -> None:
        """Load data from storage."""
        data = await self.store.async_load()
        if data is None:
            self.data = {
                "version": STORAGE_VERSION,
                "last_period_start": None,
                "settings": {
                    "cycle_length": 28,
                    "period_duration": 5,
                }
            }
            await self.async_save()
        else:
            self.data = cast(CyclistStorageData, data)

    async def async_save(self) -> None:
        """Save data to storage."""
        if self.data is not None:
            await self.store.async_save(self.data)
            self._notify_listeners()

    def add_listener(self, listener: callable) -> callable:
        """Add a listener."""
        self._listeners.append(listener)
        def remove_listener():
            if listener in self._listeners:
                self._listeners.remove(listener)
        return remove_listener

    def _notify_listeners(self) -> None:
        """Notify listeners of changes."""
        for listener in self._listeners:
            listener()

    @property
    def last_period_start(self) -> date | None:
        """Get last period start date."""
        if self.data and self.data["last_period_start"]:
            return date.fromisoformat(self.data["last_period_start"])
        return None

    @property
    def cycle_length(self) -> int:
        """Get cycle length."""
        return self.data["settings"]["cycle_length"] if self.data else 28

    @property
    def period_duration(self) -> int:
        """Get period duration."""
        return self.data["settings"]["period_duration"] if self.data else 5

    async def async_set_last_period_start(self, new_date: date) -> None:
        """Set last period start date."""
        if self.data:
            self.data["last_period_start"] = new_date.isoformat()
            await self.async_save()

    async def async_set_settings(self, cycle_length: int, period_duration: int) -> None:
        """Set settings."""
        if self.data:
            self.data["settings"]["cycle_length"] = cycle_length
            self.data["settings"]["period_duration"] = period_duration
            await self.async_save()
