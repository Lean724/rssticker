"""Config flow y Options flow para RSS Ticker."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_FEEDS,
    CONF_LANGUAGE,
    CONF_NAME,
    CONF_TICKERS,
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    CONTENT_MODES,
    DEDUP_OPTIONS,
    DEFAULT_CONTENT_MODE,
    DEFAULT_DEDUP_BY,
    DEFAULT_FEED_ACTIVE,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_LENGTH,
    DEFAULT_NAME,
    DEFAULT_SORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    FEED_ACTIVE,
    FEED_CATEGORY,
    FEED_COLOR,
    FEED_ID,
    FEED_NAME,
    FEED_ORDER,
    FEED_PRIORITY,
    FEED_URL,
    LANGUAGES,
    SORT_OPTIONS,
    TICKER_CONTENT_MODE,
    TICKER_DEDUP_BY,
    TICKER_EXCLUDE_CATEGORIES,
    TICKER_EXCLUDE_DOMAINS,
    TICKER_EXCLUDE_SOURCES,
    TICKER_EXCLUDE_WORDS,
    TICKER_FEED_IDS,
    TICKER_ID,
    TICKER_INCLUDE_WORDS,
    TICKER_MAX_ITEMS,
    TICKER_MAX_LENGTH,
    TICKER_NAME,
    TICKER_SORT,
    TICKER_TITLE,
    UPDATE_INTERVALS,
)

UPDATE_INTERVAL_LABELS = {
    1: "1 minuto",
    5: "5 minutos",
    10: "10 minutos",
    15: "15 minutos",
    30: "30 minutos",
    60: "60 minutos",
    0: "Manual",
}


def _update_interval_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(
                    value=str(v), label=UPDATE_INTERVAL_LABELS[v]
                )
                for v in UPDATE_INTERVALS
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _language_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=lang, label=lang)
                for lang in LANGUAGES
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


class RssTickerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow inicial de RSS Ticker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME].strip().lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_TIMEZONE: user_input.get(CONF_TIMEZONE, ""),
                    CONF_LANGUAGE: user_input[CONF_LANGUAGE],
                },
                options={CONF_FEEDS: [], CONF_TICKERS: []},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=str(DEFAULT_UPDATE_INTERVAL)
                ): _update_interval_selector(),
                vol.Optional(CONF_TIMEZONE, default=""): str,
                vol.Required(
                    CONF_LANGUAGE, default=DEFAULT_LANGUAGE
                ): _language_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RssTickerOptionsFlow()


class RssTickerOptionsFlow(OptionsFlow):
    """Options flow: administración de configuración general, feeds y tickers."""

    def __init__(self) -> None:
        self._selected_id: str | None = None

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "manage_feeds", "manage_tickers"],
        )

    # ------------------------------------------------------------------
    # Configuración general
    # ------------------------------------------------------------------
    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        entry = self.config_entry
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_TIMEZONE: user_input.get(CONF_TIMEZONE, ""),
                    CONF_LANGUAGE: user_input[CONF_LANGUAGE],
                },
            )
            return self.async_create_entry(title="", data=dict(entry.options))

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=str(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)),
                ): _update_interval_selector(),
                vol.Optional(
                    CONF_TIMEZONE, default=entry.data.get(CONF_TIMEZONE, "")
                ): str,
                vol.Required(
                    CONF_LANGUAGE,
                    default=entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                ): _language_selector(),
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)

    # ------------------------------------------------------------------
    # Feeds RSS
    # ------------------------------------------------------------------
    @property
    def _feeds(self) -> list[dict[str, Any]]:
        return list(self.config_entry.options.get(CONF_FEEDS, []))

    @property
    def _tickers(self) -> list[dict[str, Any]]:
        return list(self.config_entry.options.get(CONF_TICKERS, []))

    def _save_feeds(self, feeds: list[dict[str, Any]]) -> None:
        options = dict(self.config_entry.options)
        options[CONF_FEEDS] = feeds
        self.hass.config_entries.async_update_entry(self.config_entry, options=options)

    def _save_tickers(self, tickers: list[dict[str, Any]]) -> None:
        options = dict(self.config_entry.options)
        options[CONF_TICKERS] = tickers
        self.hass.config_entries.async_update_entry(self.config_entry, options=options)

    async def async_step_manage_feeds(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if not self._feeds:
            return self.async_show_menu(
                step_id="manage_feeds", menu_options=["add_feed", "init"]
            )
        return self.async_show_menu(
            step_id="manage_feeds",
            menu_options=[
                "add_feed",
                "edit_feed",
                "delete_feed",
                "duplicate_feed",
                "test_feed",
                "init",
            ],
        )

    def _feed_schema(self, feed: dict[str, Any] | None = None) -> vol.Schema:
        feed = feed or {}
        return vol.Schema(
            {
                vol.Required(FEED_NAME, default=feed.get(FEED_NAME, "")): str,
                vol.Required(FEED_URL, default=feed.get(FEED_URL, "")): str,
                vol.Optional(
                    FEED_CATEGORY, default=feed.get(FEED_CATEGORY, "")
                ): str,
                vol.Optional(
                    FEED_PRIORITY, default=feed.get(FEED_PRIORITY, 0)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, mode="box")
                ),
                vol.Optional(
                    FEED_ORDER, default=feed.get(FEED_ORDER, 0)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1000, mode="box")
                ),
                vol.Optional(FEED_COLOR, default=feed.get(FEED_COLOR, "")): str,
                vol.Optional(
                    FEED_ACTIVE, default=feed.get(FEED_ACTIVE, DEFAULT_FEED_ACTIVE)
                ): bool,
            }
        )

    async def async_step_add_feed(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            feeds = self._feeds
            feeds.append(
                {
                    FEED_ID: uuid.uuid4().hex,
                    FEED_NAME: user_input[FEED_NAME],
                    FEED_URL: user_input[FEED_URL],
                    FEED_CATEGORY: user_input.get(FEED_CATEGORY, ""),
                    FEED_PRIORITY: user_input.get(FEED_PRIORITY, 0),
                    FEED_ORDER: user_input.get(FEED_ORDER, 0),
                    FEED_COLOR: user_input.get(FEED_COLOR, ""),
                    FEED_ACTIVE: user_input.get(FEED_ACTIVE, True),
                }
            )
            self._save_feeds(feeds)
            return await self.async_step_manage_feeds()

        return self.async_show_form(
            step_id="add_feed", data_schema=self._feed_schema(), errors=errors
        )

    def _feed_select_schema(self) -> vol.Schema:
        options = [
            selector.SelectOptionDict(value=f[FEED_ID], label=f[FEED_NAME])
            for f in self._feeds
        ]
        return vol.Schema(
            {
                vol.Required("feed_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

    async def async_step_edit_feed(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            self._selected_id = user_input["feed_id"]
            return await self.async_step_edit_feed_form()
        return self.async_show_form(
            step_id="edit_feed", data_schema=self._feed_select_schema()
        )

    async def async_step_edit_feed_form(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        feeds = self._feeds
        feed = next((f for f in feeds if f[FEED_ID] == self._selected_id), None)
        if feed is None:
            return await self.async_step_manage_feeds()

        if user_input is not None:
            feed.update(
                {
                    FEED_NAME: user_input[FEED_NAME],
                    FEED_URL: user_input[FEED_URL],
                    FEED_CATEGORY: user_input.get(FEED_CATEGORY, ""),
                    FEED_PRIORITY: user_input.get(FEED_PRIORITY, 0),
                    FEED_ORDER: user_input.get(FEED_ORDER, 0),
                    FEED_COLOR: user_input.get(FEED_COLOR, ""),
                    FEED_ACTIVE: user_input.get(FEED_ACTIVE, True),
                }
            )
            self._save_feeds(feeds)
            return await self.async_step_manage_feeds()

        return self.async_show_form(
            step_id="edit_feed_form", data_schema=self._feed_schema(feed)
        )

    async def async_step_delete_feed(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            feed_id = user_input["feed_id"]
            feeds = [f for f in self._feeds if f[FEED_ID] != feed_id]
            self._save_feeds(feeds)
            # También se quita la referencia de los tickers que lo usaban.
            tickers = self._tickers
            changed = False
            for ticker in tickers:
                if feed_id in ticker.get(TICKER_FEED_IDS, []):
                    ticker[TICKER_FEED_IDS] = [
                        fid for fid in ticker[TICKER_FEED_IDS] if fid != feed_id
                    ]
                    changed = True
            if changed:
                self._save_tickers(tickers)
            return await self.async_step_manage_feeds()
        return self.async_show_form(
            step_id="delete_feed", data_schema=self._feed_select_schema()
        )

    async def async_step_duplicate_feed(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            feed_id = user_input["feed_id"]
            feeds = self._feeds
            original = next((f for f in feeds if f[FEED_ID] == feed_id), None)
            if original is not None:
                copy = dict(original)
                copy[FEED_ID] = uuid.uuid4().hex
                copy[FEED_NAME] = f"{original[FEED_NAME]} (copia)"
                feeds.append(copy)
                self._save_feeds(feeds)
            return await self.async_step_manage_feeds()
        return self.async_show_form(
            step_id="duplicate_feed", data_schema=self._feed_select_schema()
        )

    async def async_step_test_feed(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Prueba un feed inmediatamente y muestra cantidad/tiempo/errores."""
        if user_input is not None:
            feed_id = user_input["feed_id"]
            coordinator = self.config_entry.runtime_data
            await coordinator.async_refresh_feed(feed_id)
            status = coordinator._feed_status.get(feed_id, {})
            return self.async_show_form(
                step_id="test_feed_result",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "count": str(status.get("count", 0)),
                    "response_time": str(status.get("response_time_ms", "-")),
                    "last_update": str(status.get("last_update", "-")),
                    "error": str(status.get("error") or "Ninguno"),
                },
            )
        return self.async_show_form(
            step_id="test_feed", data_schema=self._feed_select_schema()
        )

    async def async_step_test_feed_result(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        return await self.async_step_manage_feeds()

    # ------------------------------------------------------------------
    # Tickers
    # ------------------------------------------------------------------
    async def async_step_manage_tickers(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if not self._tickers:
            return self.async_show_menu(
                step_id="manage_tickers", menu_options=["add_ticker", "init"]
            )
        return self.async_show_menu(
            step_id="manage_tickers",
            menu_options=["add_ticker", "edit_ticker", "delete_ticker", "init"],
        )

    def _feeds_multiselect(self) -> selector.SelectSelector:
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=f[FEED_ID], label=f[FEED_NAME])
                    for f in self._feeds
                ],
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    def _ticker_schema(self, ticker: dict[str, Any] | None = None) -> vol.Schema:
        ticker = ticker or {}
        return vol.Schema(
            {
                vol.Required(TICKER_NAME, default=ticker.get(TICKER_NAME, "")): str,
                vol.Optional(
                    TICKER_TITLE, default=ticker.get(TICKER_TITLE, "")
                ): str,
                vol.Optional(
                    TICKER_FEED_IDS, default=ticker.get(TICKER_FEED_IDS, [])
                ): self._feeds_multiselect(),
                vol.Required(
                    TICKER_CONTENT_MODE,
                    default=ticker.get(TICKER_CONTENT_MODE, DEFAULT_CONTENT_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CONTENT_MODES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    TICKER_SORT, default=ticker.get(TICKER_SORT, DEFAULT_SORT)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SORT_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    TICKER_DEDUP_BY,
                    default=ticker.get(TICKER_DEDUP_BY, DEFAULT_DEDUP_BY),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEDUP_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    TICKER_MAX_ITEMS,
                    default=ticker.get(TICKER_MAX_ITEMS, DEFAULT_MAX_ITEMS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=500, mode="box")
                ),
                vol.Optional(
                    TICKER_MAX_LENGTH,
                    default=ticker.get(TICKER_MAX_LENGTH, DEFAULT_MAX_LENGTH),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1000, mode="box")
                ),
                vol.Optional(
                    TICKER_INCLUDE_WORDS,
                    default=ticker.get(TICKER_INCLUDE_WORDS, ""),
                ): str,
                vol.Optional(
                    TICKER_EXCLUDE_WORDS,
                    default=ticker.get(TICKER_EXCLUDE_WORDS, ""),
                ): str,
                vol.Optional(
                    TICKER_EXCLUDE_DOMAINS,
                    default=ticker.get(TICKER_EXCLUDE_DOMAINS, ""),
                ): str,
                vol.Optional(
                    TICKER_EXCLUDE_CATEGORIES,
                    default=ticker.get(TICKER_EXCLUDE_CATEGORIES, ""),
                ): str,
                vol.Optional(
                    TICKER_EXCLUDE_SOURCES,
                    default=ticker.get(TICKER_EXCLUDE_SOURCES, ""),
                ): str,
            }
        )

    def _ticker_from_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        return {
            TICKER_NAME: user_input[TICKER_NAME],
            TICKER_TITLE: user_input.get(TICKER_TITLE, ""),
            TICKER_FEED_IDS: user_input.get(TICKER_FEED_IDS, []),
            TICKER_CONTENT_MODE: user_input[TICKER_CONTENT_MODE],
            TICKER_SORT: user_input[TICKER_SORT],
            TICKER_DEDUP_BY: user_input[TICKER_DEDUP_BY],
            TICKER_MAX_ITEMS: user_input.get(TICKER_MAX_ITEMS, DEFAULT_MAX_ITEMS),
            TICKER_MAX_LENGTH: user_input.get(TICKER_MAX_LENGTH, DEFAULT_MAX_LENGTH),
            TICKER_INCLUDE_WORDS: user_input.get(TICKER_INCLUDE_WORDS, ""),
            TICKER_EXCLUDE_WORDS: user_input.get(TICKER_EXCLUDE_WORDS, ""),
            TICKER_EXCLUDE_DOMAINS: user_input.get(TICKER_EXCLUDE_DOMAINS, ""),
            TICKER_EXCLUDE_CATEGORIES: user_input.get(TICKER_EXCLUDE_CATEGORIES, ""),
            TICKER_EXCLUDE_SOURCES: user_input.get(TICKER_EXCLUDE_SOURCES, ""),
        }

    async def async_step_add_ticker(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            tickers = self._tickers
            new_ticker = {TICKER_ID: uuid.uuid4().hex, **self._ticker_from_input(user_input)}
            tickers.append(new_ticker)
            self._save_tickers(tickers)
            return await self.async_step_manage_tickers()
        return self.async_show_form(
            step_id="add_ticker", data_schema=self._ticker_schema()
        )

    def _ticker_select_schema(self) -> vol.Schema:
        options = [
            selector.SelectOptionDict(value=t[TICKER_ID], label=t[TICKER_NAME])
            for t in self._tickers
        ]
        return vol.Schema(
            {
                vol.Required("ticker_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

    async def async_step_edit_ticker(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            self._selected_id = user_input["ticker_id"]
            return await self.async_step_edit_ticker_form()
        return self.async_show_form(
            step_id="edit_ticker", data_schema=self._ticker_select_schema()
        )

    async def async_step_edit_ticker_form(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        tickers = self._tickers
        ticker = next((t for t in tickers if t[TICKER_ID] == self._selected_id), None)
        if ticker is None:
            return await self.async_step_manage_tickers()

        if user_input is not None:
            ticker.update(self._ticker_from_input(user_input))
            self._save_tickers(tickers)
            return await self.async_step_manage_tickers()

        return self.async_show_form(
            step_id="edit_ticker_form", data_schema=self._ticker_schema(ticker)
        )

    async def async_step_delete_ticker(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            ticker_id = user_input["ticker_id"]
            tickers = [t for t in self._tickers if t[TICKER_ID] != ticker_id]
            self._save_tickers(tickers)
            return await self.async_step_manage_tickers()
        return self.async_show_form(
            step_id="delete_ticker", data_schema=self._ticker_select_schema()
        )
