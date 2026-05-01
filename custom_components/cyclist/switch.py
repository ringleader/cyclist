"""Switch platform for Cyclist."""
from __future__ import annotations

from datetime import date
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .cycle_math import calculate_cycle_day, is_period_active
from .storage import CyclistData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [MenstruatingSwitch(cyclist_data, entry.entry_id, entry.title)]
    )


class MenstruatingSwitch(SwitchEntity):
    """Switch representing current menstruation state."""

    _attr_has_entity_name = True
    _attr_translation_key = "menstruating"
    _attr_icon = "mdi:water"

    def __init__(self, data: CyclistData, entry_id: str, name: str) -> None:
        """Initialize the switch."""
        self.cyclist_data = data
        self._attr_unique_id = f"{entry_id}_menstruating"
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
    def is_on(self) -> bool | None:
        """Return true if currently menstruating."""
        last_start = self.cyclist_data.last_period_start
        if not last_start:
            return None
        cycle_day = calculate_cycle_day(date.today(), last_start)
        return is_period_active(cycle_day, self.cyclist_data.period_duration)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Log period start today."""
        await self.cyclist_data.async_set_last_period_start(date.today())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turning off doesn't reset the cycle, just reflects state."""
        # Optional: could adjust period_duration if we wanted to be fancy, 
        # but for now it's just a state indicator.
        pass
