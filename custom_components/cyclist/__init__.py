"""The Cyclist integration."""
from __future__ import annotations

import logging
from datetime import date
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import (
    DOMAIN, 
    CONF_CYCLE_LENGTH, 
    CONF_PERIOD_DURATION, 
    CONF_LAST_PERIOD_START, 
    CONF_GOAL,
    DEFAULT_GOAL,
    SYMPTOMS,
    ATTR_BBT,
    ATTR_CM,
    ATTR_LH,
    CM_TYPES,
    LH_RESULTS,
)
from .storage import CyclistData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.BUTTON, Platform.SWITCH, Platform.NUMBER]

SERVICE_LOG_PERIOD_START = "log_period_start"
SERVICE_UPDATE_SETTINGS = "update_settings"
SERVICE_LOG_SYMPTOM = "log_symptom"
SERVICE_LOG_BBT = "log_bbt"
SERVICE_LOG_CM = "log_cm"
SERVICE_LOG_LH = "log_lh"
SERVICE_SHIFT_PREDICTION = "shift_prediction"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cyclist from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Pass entry_id to storage for isolation
    cyclist_data = CyclistData(hass, entry.entry_id)
    await cyclist_data.async_load()

    # Apply settings from config entry or options
    cycle_length = entry.options.get(CONF_CYCLE_LENGTH, entry.data.get(CONF_CYCLE_LENGTH, 28))
    period_duration = entry.options.get(CONF_PERIOD_DURATION, entry.data.get(CONF_PERIOD_DURATION, 5))
    goal = entry.options.get(CONF_GOAL, entry.data.get(CONF_GOAL, DEFAULT_GOAL))
    
    # Get last period start
    last_start_val = entry.options.get(CONF_LAST_PERIOD_START)
    if not last_start_val:
        last_start_val = entry.data.get(CONF_LAST_PERIOD_START)
        
    if last_start_val:
        if isinstance(last_start_val, str):
            last_start_date = date.fromisoformat(last_start_val)
        else:
            last_start_date = last_start_val
        await cyclist_data.async_set_last_period_start(last_start_date)
    
    await cyclist_data.async_set_settings(cycle_length, period_duration, goal)

    hass.data[DOMAIN][entry.entry_id] = cyclist_data

    entry.async_on_remove(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Periodic rollover check
    async def check_rollover_periodically(_now: Any) -> None:
        """Periodic task to check for cycle rollover."""
        await cyclist_data.async_check_rollover()

    # Check once an hour
    from homeassistant.helpers.event import async_track_time_interval
    from datetime import timedelta
    entry.async_on_remove(
        async_track_time_interval(hass, check_rollover_periodically, timedelta(hours=1))
    )

    # Register services
    if not hass.services.has_service(DOMAIN, SERVICE_LOG_PERIOD_START):
        async def handle_log_period_start(call: ServiceCall) -> None:
            log_date = call.data.get("date", date.today())
            if log_date > date.today():
                raise ValueError("Cannot log a period start in the future")
            
            # Find target entries
            ent_reg = er.async_get(hass)
            entry_ids = set()
            
            if "device_id" in call.data:
                # Handle device targets if needed, but integration-wide logic usually hits entry_ids
                pass 

            # Simpler logic: update all entries that match the service target
            # In Home Assistant, the UI handles target filtering.
            # We just need to find which of our data objects are being called.
            
            for entry_id, data in hass.data[DOMAIN].items():
                # For now, apply to all. In a production multi-user HA, 
                # you'd filter by call.context or call.data targets.
                await data.async_set_last_period_start(log_date)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_PERIOD_START,
            handle_log_period_start,
            schema=vol.Schema({vol.Optional("date"): cv.date}),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE_SETTINGS):
        async def handle_update_settings(call: ServiceCall) -> None:
            for entry_id, data in hass.data[DOMAIN].items():
                c_len = call.data.get("cycle_length", data.cycle_length)
                p_dur = call.data.get("period_duration", data.period_duration)
                goal_val = call.data.get("goal", data.goal)
                if c_len <= p_dur:
                    continue # Skip invalid targets
                await data.async_set_settings(c_len, p_dur, goal_val)

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_SETTINGS,
            handle_update_settings,
            schema=vol.Schema({
                vol.Optional("cycle_length"): vol.All(vol.Coerce(int), vol.Range(min=15, max=60)),
                vol.Optional("period_duration"): vol.All(vol.Coerce(int), vol.Range(min=1, max=14)),
                vol.Optional("goal"): vol.In(["track", "avoid", "plan"]),
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_SYMPTOM):
        async def handle_log_symptom(call: ServiceCall) -> None:
            symptom = call.data["symptom"]
            for entry_id, data in hass.data[DOMAIN].items():
                await data.async_log_symptom(symptom)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_SYMPTOM,
            handle_log_symptom,
            schema=vol.Schema({vol.Required("symptom"): vol.In(SYMPTOMS)}),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_BBT):
        async def handle_log_bbt(call: ServiceCall) -> None:
            log_date = call.data.get("date", date.today())
            value = call.data["value"]
            for entry_id, data in hass.data[DOMAIN].items():
                await data.async_log_daily_data(log_date, ATTR_BBT, value)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_BBT,
            handle_log_bbt,
            schema=vol.Schema({
                vol.Required("value"): vol.Coerce(float),
                vol.Optional("date"): cv.date,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_CM):
        async def handle_log_cm(call: ServiceCall) -> None:
            log_date = call.data.get("date", date.today())
            value = call.data["value"]
            for entry_id, data in hass.data[DOMAIN].items():
                await data.async_log_daily_data(log_date, ATTR_CM, value)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_CM,
            handle_log_cm,
            schema=vol.Schema({
                vol.Required("value"): vol.In(CM_TYPES),
                vol.Optional("date"): cv.date,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_LH):
        async def handle_log_lh(call: ServiceCall) -> None:
            log_date = call.data.get("date", date.today())
            value = call.data["value"]
            for entry_id, data in hass.data[DOMAIN].items():
                await data.async_log_daily_data(log_date, ATTR_LH, value)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_LH,
            handle_log_lh,
            schema=vol.Schema({
                vol.Required("value"): vol.In(LH_RESULTS),
                vol.Optional("date"): cv.date,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SHIFT_PREDICTION):
        async def handle_shift_prediction(call: ServiceCall) -> None:
            offset = call.data["offset"]
            for entry_id, data in hass.data[DOMAIN].items():
                await data.async_set_prediction_offset(offset)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SHIFT_PREDICTION,
            handle_shift_prediction,
            schema=vol.Schema({
                vol.Required("offset"): vol.Coerce(int),
            }),
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
        hass.services.async_remove(DOMAIN, SERVICE_LOG_SYMPTOM)
        hass.services.async_remove(DOMAIN, SERVICE_LOG_BBT)
        hass.services.async_remove(DOMAIN, SERVICE_LOG_CM)
        hass.services.async_remove(DOMAIN, SERVICE_LOG_LH)

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    cyclist_data: CyclistData = hass.data[DOMAIN][entry.entry_id]
    
    cycle_length = entry.options.get(CONF_CYCLE_LENGTH, entry.data.get(CONF_CYCLE_LENGTH, 28))
    period_duration = entry.options.get(CONF_PERIOD_DURATION, entry.data.get(CONF_PERIOD_DURATION, 5))
    goal = entry.options.get(CONF_GOAL, entry.data.get(CONF_GOAL, DEFAULT_GOAL))
    
    # Handle date from options
    last_start_val = entry.options.get(CONF_LAST_PERIOD_START)
    if last_start_val:
        if isinstance(last_start_val, str):
            last_start_date = date.fromisoformat(last_start_val)
        else:
            last_start_date = last_start_val
        await cyclist_data.async_set_last_period_start(last_start_date)
    
    await cyclist_data.async_set_settings(cycle_length, period_duration, goal)
