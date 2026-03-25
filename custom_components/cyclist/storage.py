"""Storage layer for Cyclist."""
from __future__ import annotations

import logging
from typing import Any, TypedDict, cast
from datetime import date, datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, DOMAIN, GOAL_TRACK

_LOGGER = logging.getLogger(__name__)

class CyclistSettings(TypedDict):
    cycle_length: int
    period_duration: int
    goal: str

class CyclistStorageData(TypedDict):
    version: int
    last_period_start: str | None
    settings: CyclistSettings
    symptoms: dict[str, str] # symptom_name -> iso_timestamp
    daily_logs: dict[str, dict[str, Any]] # date_str -> {bbt, cm, lh}

class CyclistData:
    """Manages Cyclist data."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize."""
        self.hass = hass
        # Unique storage key per instance
        self.store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
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
                    "goal": GOAL_TRACK,
                },
                "symptoms": {},
                "daily_logs": {}
            }
            await self.async_save()
        else:
            self.data = cast(CyclistStorageData, data)
            # Migration/Defaults
            if "goal" not in self.data["settings"]:
                self.data["settings"]["goal"] = GOAL_TRACK
            if "symptoms" not in self.data:
                self.data["symptoms"] = {}
            if "daily_logs" not in self.data:
                self.data["daily_logs"] = {}

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

    @property
    def goal(self) -> str:
        """Get goal."""
        return self.data["settings"].get("goal", GOAL_TRACK) if self.data else GOAL_TRACK

    @property
    def symptoms(self) -> dict[str, str]:
        """Get logged symptoms."""
        return self.data.get("symptoms", {}) if self.data else {}

    async def async_set_last_period_start(self, new_date: date) -> None:
        """Set last period start date."""
        if self.data:
            self.data["last_period_start"] = new_date.isoformat()
            await self.async_save()

    async def async_set_settings(self, cycle_length: int, period_duration: int, goal: str | None = None) -> None:
        """Set settings."""
        if self.data:
            self.data["settings"]["cycle_length"] = cycle_length
            self.data["settings"]["period_duration"] = period_duration
            if goal:
                self.data["settings"]["goal"] = goal
            await self.async_save()

    async def async_log_symptom(self, symptom: str) -> None:
        """Log a symptom with current timestamp."""
        if self.data:
            if "symptoms" not in self.data:
                self.data["symptoms"] = {}
            self.data["symptoms"][symptom] = datetime.now().isoformat()
            await self.async_save()

    @property
    def daily_logs(self) -> dict[str, dict[str, Any]]:
        """Get daily logs."""
        return self.data.get("daily_logs", {}) if self.data else {}

    async def async_log_daily_data(self, log_date: date, key: str, value: Any) -> None:
        """Log daily data for a specific date."""
        if not self.data:
            return
            
        date_str = log_date.isoformat()
        if "daily_logs" not in self.data:
            self.data["daily_logs"] = {}
            
        if date_str not in self.data["daily_logs"]:
            self.data["daily_logs"][date_str] = {}
            
        self.data["daily_logs"][date_str][key] = value
        await self.async_save()
