"""Servicios expuestos por RSS Ticker."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_TICKER_ID,
    DOMAIN,
    SERVICE_CLEAR_CACHE,
    SERVICE_REFRESH,
    SERVICE_REFRESH_TICKER,
)
from .coordinator import RssTickerCoordinator

REFRESH_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}
)

REFRESH_TICKER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TICKER_ID): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)

CLEAR_CACHE_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}
)


def _coordinators(hass: HomeAssistant, entry_id: str | None) -> list[RssTickerCoordinator]:
    all_coordinators = [
        c for k, c in hass.data.get(DOMAIN, {}).items() if isinstance(c, RssTickerCoordinator)
    ]
    if entry_id:
        return [c for c in all_coordinators if c.entry.entry_id == entry_id]
    return all_coordinators


def async_setup_services(hass: HomeAssistant) -> None:
    """Registra los servicios de RSS Ticker (idempotente)."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def _handle_refresh(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        for coordinator in _coordinators(hass, entry_id):
            await coordinator.async_request_refresh()

    async def _handle_refresh_ticker(call: ServiceCall) -> None:
        ticker_id = call.data[ATTR_TICKER_ID]
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        for coordinator in _coordinators(hass, entry_id):
            await coordinator.async_refresh_ticker(ticker_id)

    async def _handle_clear_cache(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        for coordinator in _coordinators(hass, entry_id):
            coordinator.clear_cache()
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, _handle_refresh, schema=REFRESH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_TICKER,
        _handle_refresh_ticker,
        schema=REFRESH_TICKER_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_CACHE, _handle_clear_cache, schema=CLEAR_CACHE_SCHEMA
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Elimina los servicios de RSS Ticker cuando no queda ninguna entrada activa."""
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_TICKER)
    hass.services.async_remove(DOMAIN, SERVICE_CLEAR_CACHE)
