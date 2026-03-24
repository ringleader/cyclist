"""Calendar platform for Cyclist."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .storage import CyclistData
from .cycle_math import calculate_fertility_window

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CyclistCalendar(cyclist_data, entry.entry_id)])

class CyclistCalendar(CalendarEntity):
    """Calendar entity for Cyclist predictions."""

    _attr_has_entity_name = True
    _attr_name = "Predictions"

    def __init__(self, data: CyclistData, entry_id: str) -> None:
        """Initialize the calendar."""
        self.cyclist_data = data
        self._attr_unique_id = f"{entry_id}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Cyclist",
        }
        self._events: list[CalendarEvent] = []

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.cyclist_data.add_listener(self._update_events)
        )
        self._update_events()

    def _update_events(self) -> None:
        """Update calendar events."""
        self._events.clear()
        
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            self.async_write_ha_state()
            return
            
        cycle_length = self.cyclist_data.cycle_length
        period_duration = self.cyclist_data.period_duration
        fw_start, fw_end = calculate_fertility_window(cycle_length)
        
        # Generate for current + next 3 cycles (total 4)
        for i in range(4):
            cycle_start_date = last_start + timedelta(days=i * cycle_length)
            
            # Period Event
            period_end_date = cycle_start_date + timedelta(days=period_duration)
            self._events.append(
                CalendarEvent(
                    summary="Predicted Period",
                    start=cycle_start_date,
                    end=period_end_date,
                    description="Estimated period based on your configured cycle settings.",
                )
            )
            
            # Fertile Window Event
            fw_start_date = cycle_start_date + timedelta(days=fw_start - 1)
            # End date is exclusive in HA calendars, so add 1 to the end day
            fw_end_date = cycle_start_date + timedelta(days=fw_end) 
            
            self._events.append(
                CalendarEvent(
                    summary="Predicted Fertile Window",
                    start=fw_start_date,
                    end=fw_end_date,
                    description="Estimated fertile window. This is not medical advice.",
                )
            )
            
        self.async_write_ha_state()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        if not self._events:
            return None
            
        now = dt_util.now().date()
        upcoming = [e for e in self._events if e.end >= now]
        if not upcoming:
            return None
            
        # Sort by start date
        upcoming.sort(key=lambda e: e.start)
        return upcoming[0]

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        start_date_local = start_date.date()
        end_date_local = end_date.date()
        
        return [
            event
            for event in self._events
            if event.start <= end_date_local and event.end >= start_date_local
        ]
