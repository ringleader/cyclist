"""The Cyclist integration."""
from __future__ import annotations

import logging
from datetime import date
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .storage import CyclistData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]

SERVICE_LOG_PERIOD_START = "log_period_start"
SERVICE_UPDATE_SETTINGS = "update_settings"

LOG_PERIOD_START_SCHEMA = vol.Schema(
    {
        vol.Optional("date"): cv.date,
    }
)

UPDATE_SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Optional("cycle_length"): vol.All(vol.Coerce(int), vol.Range(min=15, max=60)),
        vol.Optional("period_duration"): vol.All(vol.Coerce(int), vol.Range(min=1, max=14)),
    }
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cyclist from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    cyclist_data = CyclistData(hass)
    await cyclist_data.async_load()

    cycle_length = entry.options.get("cycle_length", entry.data.get("cycle_length", 28))
    period_duration = entry.options.get("period_duration", entry.data.get("period_duration", 5))
    
    await cyclist_data.async_set_settings(cycle_length, period_duration)

    hass.data[DOMAIN][entry.entry_id] = cyclist_data

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    if not hass.services.has_service(DOMAIN, SERVICE_LOG_PERIOD_START):
        async def handle_log_period_start(call: ServiceCall) -> None:
            log_date = call.data.get("date", date.today())
            if log_date > date.today():
                raise ValueError("Cannot log a period start in the future")
            # Apply to all entries
            for data in hass.data[DOMAIN].values():
                await data.async_set_last_period_start(log_date)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_PERIOD_START,
            handle_log_period_start,
            schema=LOG_PERIOD_START_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE_SETTINGS):
        async def handle_update_settings(call: ServiceCall) -> None:
            # Apply to all entries
            for data in hass.data[DOMAIN].values():
                c_len = call.data.get("cycle_length", data.cycle_length)
                p_dur = call.data.get("period_duration", data.period_duration)
                if c_len <= p_dur:
                    raise ValueError("Cycle length must be greater than period duration.")
                await data.async_set_settings(c_len, p_dur)

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_SETTINGS,
            handle_update_settings,
            schema=UPDATE_SETTINGS_SCHEMA,
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_LOG_PERIOD_START)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SETTINGS)

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]
    
    cycle_length = entry.options.get("cycle_length", entry.data.get("cycle_length", 28))
    period_duration = entry.options.get("period_duration", entry.data.get("period_duration", 5))
    
    await cyclist_data.async_set_settings(cycle_length, period_duration)
