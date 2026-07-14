"""DataUpdateCoordinator para RSS Ticker."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_FEEDS,
    CONF_TICKERS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    EVENT_ERROR,
    EVENT_UPDATED,
    FEED_ACTIVE,
    STATUS_NO_DATA,
    STATUS_OK,
    STATUS_STALE,
    TICKER_FEED_IDS,
    TICKER_ID,
)
from .helpers import FeedItem, async_fetch_feed, filter_and_sort_items

_LOGGER = logging.getLogger(__name__)


class RssTickerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordina la descarga periódica de feeds y el armado de tickers."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        interval_minutes = entry.data.get(CONF_UPDATE_INTERVAL, 10)
        update_interval = (
            timedelta(minutes=interval_minutes) if interval_minutes else None
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )

        # Caché del último resultado válido por feed_id, usada cuando un feed
        # falla en una actualización posterior.
        self._feed_cache: dict[str, list[FeedItem]] = {}
        self._feed_status: dict[str, dict[str, Any]] = {}

    @property
    def feeds(self) -> list[dict[str, Any]]:
        return self.entry.options.get(CONF_FEEDS, self.entry.data.get(CONF_FEEDS, []))

    @property
    def tickers(self) -> list[dict[str, Any]]:
        return self.entry.options.get(
            CONF_TICKERS, self.entry.data.get(CONF_TICKERS, [])
        )

    def clear_cache(self) -> None:
        """Vacía la caché de feeds en memoria."""
        self._feed_cache.clear()
        self._feed_status.clear()

    async def _async_update_data(self) -> dict[str, Any]:
        """Descarga todos los feeds activos y arma los datos de cada ticker."""
        session = async_get_clientsession(self.hass)
        active_feeds = [f for f in self.feeds if f.get(FEED_ACTIVE, True)]

        await self._async_refresh_feeds(session, active_feeds)

        return self._build_result()

    async def async_refresh_feed(self, feed_id: str) -> None:
        """Refresca un único feed bajo demanda (usado por el botón 'Probar RSS')."""
        feed_conf = next((f for f in self.feeds if f["id"] == feed_id), None)
        if feed_conf is None:
            return
        session = async_get_clientsession(self.hass)
        await self._async_refresh_feeds(session, [feed_conf])
        self.async_set_updated_data(self._build_result())

    async def async_refresh_ticker(self, ticker_id: str) -> None:
        """Refresca únicamente los feeds usados por un ticker específico."""
        ticker_conf = next((t for t in self.tickers if t[TICKER_ID] == ticker_id), None)
        if ticker_conf is None:
            return
        feed_ids = set(ticker_conf.get(TICKER_FEED_IDS, []))
        feeds_to_refresh = [f for f in self.feeds if f["id"] in feed_ids]
        session = async_get_clientsession(self.hass)
        await self._async_refresh_feeds(session, feeds_to_refresh)
        self.async_set_updated_data(self._build_result())

    async def _async_refresh_feeds(
        self, session: aiohttp.ClientSession, feeds: list[dict[str, Any]]
    ) -> None:
        for feed_conf in feeds:
            feed_id = feed_conf["id"]
            result = await async_fetch_feed(session, feed_conf)

            if result.ok:
                self._feed_cache[feed_id] = result.items
                self._feed_status[feed_id] = {
                    "status": STATUS_OK,
                    "error": None,
                    "response_time_ms": result.response_time_ms,
                    "last_update": result.fetched_at,
                    "count": len(result.items),
                }
            else:
                has_cache = feed_id in self._feed_cache
                self._feed_status[feed_id] = {
                    "status": STATUS_STALE if has_cache else STATUS_NO_DATA,
                    "error": result.error,
                    "response_time_ms": result.response_time_ms,
                    "last_update": self._feed_status.get(feed_id, {}).get(
                        "last_update"
                    ),
                    "count": len(self._feed_cache.get(feed_id, [])),
                }
                _LOGGER.warning(
                    "No se pudo actualizar el feed '%s': %s",
                    feed_conf.get("name", feed_id),
                    result.error,
                )
                self.hass.bus.async_fire(
                    EVENT_ERROR,
                    {
                        "entry_id": self.entry.entry_id,
                        "feed_id": feed_id,
                        "feed_name": feed_conf.get("name", feed_id),
                        "error": result.error,
                    },
                )

    def _build_result(self) -> dict[str, Any]:
        tickers_result: dict[str, Any] = {}

        for ticker_conf in self.tickers:
            ticker_id = ticker_conf[TICKER_ID]
            feed_ids = ticker_conf.get(TICKER_FEED_IDS, [])

            all_items: list[FeedItem] = []
            sources: list[str] = []
            errors: list[dict[str, Any]] = []
            worst_status = STATUS_OK

            for feed_id in feed_ids:
                feed_conf = next((f for f in self.feeds if f["id"] == feed_id), None)
                if feed_conf is None:
                    continue
                sources.append(feed_conf.get("name", feed_id))
                all_items.extend(self._feed_cache.get(feed_id, []))

                status_info = self._feed_status.get(feed_id)
                if status_info and status_info["status"] != STATUS_OK:
                    errors.append(
                        {
                            "feed": feed_conf.get("name", feed_id),
                            "error": status_info.get("error"),
                        }
                    )
                    if status_info["status"] == STATUS_NO_DATA:
                        worst_status = STATUS_NO_DATA
                    elif worst_status != STATUS_NO_DATA:
                        worst_status = STATUS_STALE

            filtered_items = filter_and_sort_items(all_items, ticker_conf)

            last_update = max(
                (
                    self._feed_status.get(fid, {}).get("last_update")
                    for fid in feed_ids
                    if self._feed_status.get(fid, {}).get("last_update")
                ),
                default=None,
            )

            tickers_result[ticker_id] = {
                "name": ticker_conf.get("name", ticker_id),
                "title": ticker_conf.get("title", ""),
                "items": [item.as_dict() for item in filtered_items],
                "count": len(filtered_items),
                "sources": sources,
                "status": worst_status,
                "errors": errors,
                "last_update": last_update.isoformat() if last_update else None,
            }

            self.hass.bus.async_fire(
                EVENT_UPDATED,
                {
                    "entry_id": self.entry.entry_id,
                    "ticker_id": ticker_id,
                    "count": len(filtered_items),
                },
            )

        return {
            "tickers": tickers_result,
            "updated_at": datetime.now(UTC).isoformat(),
        }
