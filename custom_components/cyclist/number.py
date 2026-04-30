"""Number platform for Cyclist."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .storage import CyclistData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            CycleLengthNumber(cyclist_data, entry.entry_id, entry.title),
            PeriodDurationNumber(cyclist_data, entry.entry_id, entry.title),
        ]
    )


class CyclistNumber(NumberEntity):
    """Base class for Cyclist numbers."""

    _attr_has_entity_name = True

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        """Initialize the number."""
        self.cyclist_data = data
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": name,
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.cyclist_data.add_listener(self.async_write_ha_state)
        )


class CycleLengthNumber(CyclistNumber):
    """Number for cycle length."""

    _attr_translation_key = "cycle_length"
    _attr_icon = "mdi:calendar-range"
    _attr_native_min_value = 15
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "days"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_cycle_length"

    @property
    def native_value(self) -> float:
        """Return the current cycle length."""
        return float(self.cyclist_data.cycle_length)

    async def async_set_native_value(self, value: float) -> None:
        """Update cycle length."""
        await self.cyclist_data.async_set_settings(
            cycle_length=int(value),
            period_duration=self.cyclist_data.period_duration,
            goal=self.cyclist_data.goal
        )


class PeriodDurationNumber(CyclistNumber):
    """Number for period duration."""

    _attr_translation_key = "period_duration"
    _attr_icon = "mdi:water-percent"
    _attr_native_min_value = 1
    _attr_native_max_value = 14
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "days"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_period_duration"

    @property
    def native_value(self) -> float:
        """Return the current period duration."""
        return float(self.cyclist_data.period_duration)

    async def async_set_native_value(self, value: float) -> None:
        """Update period duration."""
        await self.cyclist_data.async_set_settings(
            cycle_length=self.cyclist_data.cycle_length,
            period_duration=int(value),
            goal=self.cyclist_data.goal
        )
