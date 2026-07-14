"""Constantes para la integración RSS Ticker."""
from __future__ import annotations

DOMAIN = "rssticker"
PLATFORMS = ["sensor"]

MANUFACTURER = "Lean724"

# ---------------------------------------------------------------------------
# Configuración inicial (ConfigFlow)
# ---------------------------------------------------------------------------
CONF_NAME = "name"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_TIMEZONE = "timezone"
CONF_LANGUAGE = "language"

DEFAULT_NAME = "RSS Ticker"
DEFAULT_UPDATE_INTERVAL = 10  # minutos

# Intervalos de actualización soportados (minutos). 0 = manual.
UPDATE_INTERVALS = [1, 5, 10, 15, 30, 60, 0]

LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"

# ---------------------------------------------------------------------------
# Opciones (OptionsFlow) - Feeds RSS
# ---------------------------------------------------------------------------
CONF_FEEDS = "feeds"

FEED_ID = "id"
FEED_NAME = "name"
FEED_URL = "url"
FEED_CATEGORY = "category"
FEED_PRIORITY = "priority"
FEED_ORDER = "order"
FEED_COLOR = "color"
FEED_ACTIVE = "active"

DEFAULT_FEED_PRIORITY = 0
DEFAULT_FEED_ORDER = 0
DEFAULT_FEED_ACTIVE = True

# ---------------------------------------------------------------------------
# Opciones (OptionsFlow) - Tickers
# ---------------------------------------------------------------------------
CONF_TICKERS = "tickers"

TICKER_ID = "id"
TICKER_NAME = "name"
TICKER_TITLE = "title"
TICKER_FEED_IDS = "feed_ids"

TICKER_CONTENT_MODE = "content_mode"
CONTENT_MODE_TITLE = "title_only"
CONTENT_MODE_TITLE_DESC = "title_description"
CONTENT_MODE_TITLE_CONTENT = "title_content"
CONTENT_MODES = [
    CONTENT_MODE_TITLE,
    CONTENT_MODE_TITLE_DESC,
    CONTENT_MODE_TITLE_CONTENT,
]
DEFAULT_CONTENT_MODE = CONTENT_MODE_TITLE_DESC

TICKER_SORT = "sort"
SORT_NEWEST = "newest"
SORT_OLDEST = "oldest"
SORT_RANDOM = "random"
SORT_OPTIONS = [SORT_NEWEST, SORT_OLDEST, SORT_RANDOM]
DEFAULT_SORT = SORT_NEWEST

TICKER_DEDUP_BY = "dedup_by"
DEDUP_GUID = "guid"
DEDUP_TITLE = "title"
DEDUP_URL = "url"
DEDUP_NONE = "none"
DEDUP_OPTIONS = [DEDUP_GUID, DEDUP_TITLE, DEDUP_URL, DEDUP_NONE]
DEFAULT_DEDUP_BY = DEDUP_GUID

TICKER_MAX_ITEMS = "max_items"
DEFAULT_MAX_ITEMS = 50

TICKER_MAX_LENGTH = "max_length"
DEFAULT_MAX_LENGTH = 0  # 0 = sin límite

TICKER_INCLUDE_WORDS = "include_words"
TICKER_EXCLUDE_WORDS = "exclude_words"
TICKER_EXCLUDE_DOMAINS = "exclude_domains"
TICKER_EXCLUDE_CATEGORIES = "exclude_categories"
TICKER_EXCLUDE_SOURCES = "exclude_sources"

# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------
SERVICE_REFRESH = "refresh"
SERVICE_REFRESH_TICKER = "refresh_ticker"
SERVICE_CLEAR_CACHE = "clear_cache"

ATTR_TICKER_ID = "ticker_id"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"

# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------
EVENT_UPDATED = f"{DOMAIN}_updated"
EVENT_ERROR = f"{DOMAIN}_error"

# ---------------------------------------------------------------------------
# Misceláneo
# ---------------------------------------------------------------------------
FEED_TIMEOUT = 15  # segundos
HTTP_USER_AGENT = "Home Assistant RSS Ticker/1.0 (+https://github.com/Lean724/rssticker)"

STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_STALE = "stale"  # usando último contenido válido en caché
STATUS_NO_DATA = "no_data"

CARD_URL = "/rssticker-card/rssticker-card.js"
CARD_NAME = "rssticker-card.js"
