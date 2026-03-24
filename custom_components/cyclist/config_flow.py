"""Config flow for Cyclist integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_CYCLE_LENGTH,
    CONF_PERIOD_DURATION,
    DEFAULT_CYCLE_LENGTH,
    DEFAULT_PERIOD_DURATION,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CYCLE_LENGTH, default=DEFAULT_CYCLE_LENGTH): int,
        vol.Required(CONF_PERIOD_DURATION, default=DEFAULT_PERIOD_DURATION): int,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cyclist."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors = {}
        if user_input is not None:
            if user_input[CONF_CYCLE_LENGTH] <= user_input[CONF_PERIOD_DURATION]:
                errors["base"] = "invalid_length"
            else:
                return self.async_create_entry(title="Cyclist", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
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

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CYCLE_LENGTH,
                        default=self.config_entry.options.get(
                            CONF_CYCLE_LENGTH,
                            self.config_entry.data.get(CONF_CYCLE_LENGTH, DEFAULT_CYCLE_LENGTH),
                        ),
                    ): int,
                    vol.Required(
                        CONF_PERIOD_DURATION,
                        default=self.config_entry.options.get(
                            CONF_PERIOD_DURATION,
                            self.config_entry.data.get(CONF_PERIOD_DURATION, DEFAULT_PERIOD_DURATION),
                        ),
                    ): int,
                }
            ),
            errors=errors,
        )
