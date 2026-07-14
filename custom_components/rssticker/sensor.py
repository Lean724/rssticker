"""Plataforma sensor para RSS Ticker."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN, MANUFACTURER, TICKER_ID
from .coordinator import RssTickerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea un sensor por cada ticker definido en la entrada de configuración."""
    coordinator: RssTickerCoordinator = entry.runtime_data

    entities = [
        RssTickerSensor(coordinator, entry, ticker_conf[TICKER_ID])
        for ticker_conf in coordinator.tickers
    ]
    async_add_entities(entities)


class RssTickerSensor(CoordinatorEntity[RssTickerCoordinator], SensorEntity):
    """Sensor que representa un ticker (grupo de feeds RSS)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:rss"
    _attr_native_unit_of_measurement = "noticias"

    def __init__(
        self, coordinator: RssTickerCoordinator, entry: ConfigEntry, ticker_id: str
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._ticker_id = ticker_id
        self._attr_unique_id = f"{entry.entry_id}_{ticker_id}"
        self._attr_translation_key = "ticker"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_NAME, "RSS Ticker"),
            manufacturer=MANUFACTURER,
            model="RSS Ticker",
        )

    @property
    def _ticker_data(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("tickers", {}).get(
            self._ticker_id, {}
        )

    @property
    def name(self) -> str:
        return self._ticker_data.get("name", self._ticker_id)

    @property
    def native_value(self) -> int:
        return self._ticker_data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._ticker_data
        return {
            "title": data.get("title", ""),
            "items": data.get("items", []),
            "sources": data.get("sources", []),
            "status": data.get("status"),
            "errors": data.get("errors", []),
            "last_update": data.get("last_update"),
        }
