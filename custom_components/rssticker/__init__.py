"""Integración RSS Ticker para Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CARD_NAME, CARD_URL, DOMAIN, PLATFORMS
from .coordinator import RssTickerCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

CARD_DIR = Path(__file__).parent / "www"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura RSS Ticker a partir de una entrada de configuración."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = RssTickerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await _async_register_card(hass)
    async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarga una entrada de configuración."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            async_unload_services(hass)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Se llama cuando cambian las opciones (feeds/tickers) de la entrada."""
    coordinator: RssTickerCoordinator = entry.runtime_data
    await coordinator.async_request_refresh()


async def _async_register_card(hass: HomeAssistant) -> None:
    """Registra www/rssticker-card.js como recurso estático y de Lovelace.

    Se registra una única vez, sin importar cuántas entradas de configuración
    existan.
    """
    if hass.data[DOMAIN].get("_card_registered"):
        return

    if not CARD_DIR.exists():
        _LOGGER.warning(
            "No se encontró el directorio de la tarjeta en %s; la Lovelace Card "
            "'rssticker-card' no estará disponible",
            CARD_DIR,
        )
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig("/rssticker-card", str(CARD_DIR), cache_headers=False)]
    )

    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, f"{CARD_URL}?v={_card_version()}")
    except ImportError:  # pragma: no cover - defensivo, frontend siempre disponible
        _LOGGER.debug("No se pudo registrar la tarjeta automáticamente en Lovelace")

    hass.data[DOMAIN]["_card_registered"] = True
    _LOGGER.debug("Tarjeta %s registrada en %s", CARD_NAME, CARD_URL)


def _card_version() -> str:
    """Devuelve un identificador de versión del archivo de la tarjeta (cache-busting)."""
    card_file = CARD_DIR / CARD_NAME
    if card_file.exists():
        return str(int(card_file.stat().st_mtime))
    return "1"
