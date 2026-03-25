"""Config flow for Cyclist integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_CYCLE_LENGTH,
    CONF_PERIOD_DURATION,
    CONF_LAST_PERIOD_START,
    CONF_GOAL,
    DEFAULT_CYCLE_LENGTH,
    DEFAULT_PERIOD_DURATION,
    DEFAULT_GOAL,
    GOAL_AVOID,
    GOAL_PLAN,
    GOAL_TRACK,
)

_LOGGER = logging.getLogger(__name__)

GOAL_OPTIONS = [GOAL_TRACK, GOAL_AVOID, GOAL_PLAN]

def get_user_data_schema(
    name: str = "",
    cycle_length: int = DEFAULT_CYCLE_LENGTH,
    period_duration: int = DEFAULT_PERIOD_DURATION,
    last_start: date | str = None,
    goal: str = DEFAULT_GOAL,
    is_options: bool = False,
) -> vol.Schema:
    """Return user data schema."""
    if last_start is None:
        last_start = date.today()
    if isinstance(last_start, date):
        last_start = last_start.isoformat()

    schema_dict = {}
    if not is_options:
        schema_dict[vol.Required(CONF_NAME, default=name)] = str
        
    schema_dict.update({
        vol.Required(CONF_CYCLE_LENGTH, default=cycle_length): int,
        vol.Required(CONF_PERIOD_DURATION, default=period_duration): int,
        vol.Required(CONF_LAST_PERIOD_START, default=last_start): selector.DateSelector(),
        vol.Required(CONF_GOAL, default=goal): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[GOAL_TRACK, GOAL_AVOID, GOAL_PLAN],
                translation_key="goal",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    })
    
    return vol.Schema(schema_dict)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cyclist."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_CYCLE_LENGTH] <= user_input[CONF_PERIOD_DURATION]:
                errors["base"] = "invalid_length"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user", 
            data_schema=get_user_data_schema(), 
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Cyclist."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_CYCLE_LENGTH] <= user_input[CONF_PERIOD_DURATION]:
                errors["base"] = "invalid_length"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Get current values
        current_cycle = self.config_entry.options.get(
            CONF_CYCLE_LENGTH, 
            self.config_entry.data.get(CONF_CYCLE_LENGTH, DEFAULT_CYCLE_LENGTH)
        )
        current_duration = self.config_entry.options.get(
            CONF_PERIOD_DURATION,
            self.config_entry.data.get(CONF_PERIOD_DURATION, DEFAULT_PERIOD_DURATION)
        )
        current_goal = self.config_entry.options.get(
            CONF_GOAL,
            self.config_entry.data.get(CONF_GOAL, DEFAULT_GOAL)
        )
        current_start = self.config_entry.options.get(
            CONF_LAST_PERIOD_START,
            self.config_entry.data.get(CONF_LAST_PERIOD_START, date.today().isoformat())
        )

        return self.async_show_form(
            step_id="init",
            data_schema=get_user_data_schema(
                cycle_length=current_cycle,
                period_duration=current_duration,
                last_start=current_start,
                goal=current_goal,
                is_options=True,
            ),
            errors=errors,
        )
