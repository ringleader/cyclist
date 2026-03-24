"""Sensor platform for Cyclist."""
from __future__ import annotations

from datetime import date
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .cycle_math import (
    calculate_cycle_day,
    calculate_days_until_next_period,
    get_fertility,
    get_phase,
)
from .storage import CyclistData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            CycleDaySensor(cyclist_data, entry.entry_id),
            CyclePhaseSensor(cyclist_data, entry.entry_id),
            FertilitySensor(cyclist_data, entry.entry_id),
            NextPeriodSensor(cyclist_data, entry.entry_id),
        ]
    )


class CyclistBaseSensor(SensorEntity):
    """Base class for Cyclist sensors."""

    _attr_has_entity_name = True

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        """Initialize the sensor."""
        self.cyclist_data = data
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Cyclist",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.cyclist_data.add_listener(self.async_write_ha_state)
        )

    @property
    def _status_attr(self) -> dict[str, str]:
        if not self.cyclist_data.last_period_start:
            return {"status": "no data — call cyclist.log_period_start"}
        return {}


class CycleDaySensor(CyclistBaseSensor):
    """Sensor for current cycle day."""

    _attr_translation_key = "cycle_day"
    _attr_icon = "mdi:calendar-today"
    _attr_native_unit_of_measurement = "day"

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        super().__init__(data, entry_id)
        self._attr_unique_id = f"{entry_id}_cycle_day"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        return calculate_cycle_day(date.today(), last_start)
        
    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return self._status_attr


class CyclePhaseSensor(CyclistBaseSensor):
    """Sensor for current cycle phase."""

    _attr_translation_key = "phase"
    _attr_icon = "mdi:moon-waning-crescent"

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        super().__init__(data, entry_id)
        self._attr_unique_id = f"{entry_id}_phase"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        cycle_day = calculate_cycle_day(date.today(), last_start)
        return get_phase(
            cycle_day, 
            self.cyclist_data.cycle_length, 
            self.cyclist_data.period_duration
        )

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return self._status_attr


class FertilitySensor(CyclistBaseSensor):
    """Sensor for current fertility status."""

    _attr_translation_key = "fertility"
    _attr_icon = "mdi:flower"

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        super().__init__(data, entry_id)
        self._attr_unique_id = f"{entry_id}_fertility"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        cycle_day = calculate_cycle_day(date.today(), last_start)
        return get_fertility(cycle_day, self.cyclist_data.cycle_length)
        
    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return self._status_attr


class NextPeriodSensor(CyclistBaseSensor):
    """Sensor for days until next period."""

    _attr_translation_key = "next_period"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        super().__init__(data, entry_id)
        self._attr_unique_id = f"{entry_id}_next_period"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        return calculate_days_until_next_period(
            date.today(), last_start, self.cyclist_data.cycle_length
        )
        
    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return self._status_attr
