"""Button platform for Cyclist."""
from __future__ import annotations

from datetime import date, timedelta
import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            LogPeriodTodayButton(cyclist_data, entry.entry_id, entry.title),
            LogPeriodYesterdayButton(cyclist_data, entry.entry_id, entry.title),
            LogPeriod2DaysAgoButton(cyclist_data, entry.entry_id, entry.title),
            LogPeriod3DaysAgoButton(cyclist_data, entry.entry_id, entry.title),
            LogPeriod4DaysAgoButton(cyclist_data, entry.entry_id, entry.title),
            LogPeriod5DaysAgoButton(cyclist_data, entry.entry_id, entry.title),
            DelayPredictionButton(cyclist_data, entry.entry_id, entry.title),
            AdvancePredictionButton(cyclist_data, entry.entry_id, entry.title),
        ]
    )


class CyclistButton(ButtonEntity):
    """Base class for Cyclist buttons."""

    _attr_has_entity_name = True

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        """Initialize the button."""
        self.cyclist_data = data
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": name,
        }


class LogPeriodTodayButton(CyclistButton):
    """Button to log period start today."""

    _attr_translation_key = "log_period_today"
    _attr_icon = "mdi:calendar-plus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_today"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today())


class LogPeriodYesterdayButton(CyclistButton):
    """Button to log period start yesterday."""

    _attr_translation_key = "log_period_yesterday"
    _attr_icon = "mdi:calendar-minus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_yesterday"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today() - timedelta(days=1))


class LogPeriod2DaysAgoButton(CyclistButton):
    """Button to log period start 2 days ago."""

    _attr_translation_key = "log_period_2_days_ago"
    _attr_icon = "mdi:calendar-minus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_2_days_ago"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today() - timedelta(days=2))


class LogPeriod3DaysAgoButton(CyclistButton):
    """Button to log period start 3 days ago."""

    _attr_translation_key = "log_period_3_days_ago"
    _attr_icon = "mdi:calendar-minus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_3_days_ago"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today() - timedelta(days=3))


class LogPeriod4DaysAgoButton(CyclistButton):
    """Button to log period start 4 days ago."""

    _attr_translation_key = "log_period_4_days_ago"
    _attr_icon = "mdi:calendar-minus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_4_days_ago"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today() - timedelta(days=4))


class LogPeriod5DaysAgoButton(CyclistButton):
    """Button to log period start 5 days ago."""

    _attr_translation_key = "log_period_5_days_ago"
    _attr_icon = "mdi:calendar-minus"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_log_period_5_days_ago"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.cyclist_data.async_set_last_period_start(date.today() - timedelta(days=5))


class DelayPredictionButton(CyclistButton):
    """Button to delay the next period prediction by 1 day."""

    _attr_translation_key = "delay_prediction"
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_delay_prediction"

    async def async_press(self) -> None:
        """Handle the button press."""
        current_offset = self.cyclist_data.prediction_offset
        await self.cyclist_data.async_set_prediction_offset(current_offset + 1)


class AdvancePredictionButton(CyclistButton):
    """Button to advance the next period prediction by 1 day."""

    _attr_translation_key = "advance_prediction"
    _attr_icon = "mdi:calendar-arrow-left"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        super().__init__(data, entry_id, name)
        self._attr_unique_id = f"{entry_id}_advance_prediction"

    async def async_press(self) -> None:
        """Handle the button press."""
        current_offset = self.cyclist_data.prediction_offset
        await self.cyclist_data.async_set_prediction_offset(current_offset - 1)
