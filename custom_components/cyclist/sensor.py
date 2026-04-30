"""Sensor platform for Cyclist."""
from __future__ import annotations

from datetime import date
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    WINDOW_CALENDAR,
    WINDOW_SYMPTOTHERMAL,
)
from .cycle_math import (
    calculate_cycle_day,
    calculate_days_until_next_period,
    get_fertility,
    get_fertility_status,
    get_phase,
    get_ovulation_confirmation,
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
            CycleDaySensor(cyclist_data, entry.entry_id, entry.title),
            CyclePhaseSensor(cyclist_data, entry.entry_id, entry.title),
            FertilitySensor(cyclist_data, entry.entry_id, entry.title),
            FertilityStatusSensor(cyclist_data, entry.entry_id, entry.title),
            NextPeriodSensor(cyclist_data, entry.entry_id, entry.title),
            GoalSensor(cyclist_data, entry.entry_id, entry.title),
            ConfirmedOvulationSensor(cyclist_data, entry.entry_id, entry.title),
            PeakDaySensor(cyclist_data, entry.entry_id, entry.title),
        ]
    )


class CyclistBaseSensor(SensorEntity):
    """Base class for Cyclist sensors."""

    _attr_has_entity_name = True

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        """Initialize the sensor."""
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

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return entity specific state attributes."""
        attrs = {}
        if not self.cyclist_data.last_period_start:
            attrs["status"] = "no data — call cyclist.log_period_start"
        
        # Add symptoms to all sensors for easy automation access
        for symptom, timestamp in self.cyclist_data.symptoms.items():
            attrs[f"last_{symptom}"] = timestamp
            
        # Add cycle settings (Core domain data only)
        attrs["cycle_length"] = self.cyclist_data.cycle_length
        attrs["period_duration"] = self.cyclist_data.period_duration
        attrs["goal"] = self.cyclist_data.goal
            
        return attrs


class CycleDaySensor(CyclistBaseSensor):
    """Sensor for current cycle day."""

    _attr_translation_key = "cycle_day"
    _attr_icon = "mdi:calendar-today"
    _attr_native_unit_of_measurement = "day"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_cycle_day"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        return calculate_cycle_day(date.today(), last_start)


class CyclePhaseSensor(CyclistBaseSensor):
    """Sensor for current cycle phase."""

    _attr_translation_key = "phase"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_phase"

    @property
    def icon(self) -> str:
        """Dynamic icon based on phase."""
        if self.native_value == "late":
            return "mdi:calendar-alert"
        return "mdi:moon-waning-crescent"

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


class FertilitySensor(CyclistBaseSensor):
    """Sensor for basic fertility level."""

    _attr_translation_key = "fertility"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_fertility"

    @property
    def icon(self) -> str:
        """Dynamic icon based on fertility level."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return "mdi:flower-outline"
        
        cycle_day = calculate_cycle_day(date.today(), last_start)
        level = get_fertility(
            cycle_day, 
            self.cyclist_data.cycle_length,
            last_start,
            self.cyclist_data.daily_logs
        )
        
        if level == "fertile":
            return "mdi:flower"
        if level == "low":
            return "mdi:flower-pollen"
        return "mdi:flower-outline"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        cycle_day = calculate_cycle_day(date.today(), last_start)
        return get_fertility(
            cycle_day, 
            self.cyclist_data.cycle_length,
            last_start,
            self.cyclist_data.daily_logs
        )

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return entity specific state attributes."""
        attrs = super().extra_state_attributes
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return attrs
            
        conf = get_ovulation_confirmation(
            last_start, 
            self.cyclist_data.daily_logs, 
            self.cyclist_data.cycle_length
        )
        attrs["method"] = WINDOW_SYMPTOTHERMAL if conf["methods"] else WINDOW_CALENDAR
        attrs["confirmed_ovulation_day"] = conf["confirmed_day"]
        attrs["peak_day"] = conf["peak_day"]
        attrs["tracking_methods"] = ", ".join(conf["methods"])
        return attrs


class ConfirmedOvulationSensor(CyclistBaseSensor):
    """Sensor for the day ovulation was confirmed via symptoms."""

    _attr_translation_key = "confirmed_ovulation"
    _attr_icon = "mdi:check-decagram"
    _attr_native_unit_of_measurement = "day"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_confirmed_ovulation"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
            
        conf = get_ovulation_confirmation(
            last_start, 
            self.cyclist_data.daily_logs, 
            self.cyclist_data.cycle_length
        )
        return conf["confirmed_day"]


class PeakDaySensor(CyclistBaseSensor):
    """Sensor for the detected peak day (last fertile CM or first peak LH)."""

    _attr_translation_key = "peak_day"
    _attr_icon = "mdi:summit"
    _attr_native_unit_of_measurement = "day"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_peak_day"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
            
        conf = get_ovulation_confirmation(
            last_start, 
            self.cyclist_data.daily_logs, 
            self.cyclist_data.cycle_length
        )
        return conf["peak_day"]


class FertilityStatusSensor(CyclistBaseSensor):
    """Sensor for goal-aware actionable fertility status."""

    _attr_translation_key = "fertility_status"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_fertility_status"

    @property
    def icon(self) -> str:
        """Dynamic icon based on status."""
        status = self.native_value
        if status in ["high_chance", "peak_fertility"]:
            return "mdi:alert-decagram"
        if status in ["caution", "fertility_rising"]:
            return "mdi:alert-circle-outline"
        return "mdi:check-circle-outline"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        cycle_day = calculate_cycle_day(date.today(), last_start)
        return get_fertility_status(
            cycle_day, 
            self.cyclist_data.cycle_length,
            self.cyclist_data.goal,
            last_start,
            self.cyclist_data.daily_logs
        )


class NextPeriodSensor(CyclistBaseSensor):
    """Sensor for days until next period."""

    _attr_translation_key = "next_period"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_next_period"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        return calculate_days_until_next_period(
            date.today(), 
            last_start, 
            self.cyclist_data.cycle_length,
            self.cyclist_data.prediction_offset
        )


class GoalSensor(CyclistBaseSensor):
    """Sensor for current goal."""

    _attr_translation_key = "goal"
    _attr_icon = "mdi:target"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_goal"

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self.cyclist_data.goal
