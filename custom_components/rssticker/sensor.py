"""Plataforma sensor para RSS Ticker."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
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
    """Crea y mantiene sincronizado un sensor por cada ticker de la entrada."""
    coordinator: RssTickerCoordinator = entry.runtime_data
    known_ticker_ids: set[str] = set()
    entities_by_id: dict[str, RssTickerSensor] = {}

    @callback
    def _async_sync_entities() -> None:
        current_ids = {t[TICKER_ID] for t in coordinator.tickers}

        # Agregar sensores para tickers nuevos
        new_ids = current_ids - known_ticker_ids
        if new_ids:
            new_entities: list[RssTickerSensor] = []
            for tid in new_ids:
                sensor = RssTickerSensor(coordinator, entry, tid)
                entities_by_id[tid] = sensor
                new_entities.append(sensor)
            known_ticker_ids.update(new_ids)
            async_add_entities(new_entities)

        # Eliminar sensores de tickers borrados
        removed_ids = known_ticker_ids - current_ids
        if removed_ids:
            ent_reg = er.async_get(hass)
            for tid in removed_ids:
                known_ticker_ids.discard(tid)
                sensor = entities_by_id.pop(tid, None)
                if sensor and sensor.entity_id:
                    ent_reg.async_remove(sensor.entity_id)

    _async_sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_sync_entities))


class RssTickerSensor(CoordinatorEntity[RssTickerCoordinator], SensorEntity):
    """Sensor que representa un ticker (grupo de feeds RSS)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:rss"
    _attr_native_unit_of_measurement = "items"

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
            "ticker_id": self._ticker_id,
            "title": data.get("title", ""),
            "content_mode": data.get("content_mode", "title_description"),
            "items": data.get("items", []),
            "sources": data.get("sources", []),
            "status": data.get("status"),
            "errors": data.get("errors", []),
            "last_update": data.get("last_update"),
        }
