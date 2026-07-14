"""Funciones auxiliares para descargar, parsear y filtrar feeds RSS/Atom/RDF."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp
import feedparser

from .const import (
    DEDUP_GUID,
    DEDUP_NONE,
    DEDUP_TITLE,
    FEED_TIMEOUT,
    HTTP_USER_AGENT,
    SORT_OLDEST,
    SORT_RANDOM,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class FeedItem:
    """Representa una noticia normalizada proveniente de un feed."""

    guid: str
    title: str
    description: str
    content: str
    link: str
    published: datetime | None
    source_id: str
    source_name: str
    category: str
    color: str | None
    domain: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "guid": self.guid,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "link": self.link,
            "published": self.published.isoformat() if self.published else None,
            "source": self.source_name,
            "source_id": self.source_id,
            "category": self.category,
            "color": self.color,
            "domain": self.domain,
        }


@dataclass
class FeedFetchResult:
    """Resultado de intentar descargar y parsear un feed."""

    feed_id: str
    ok: bool
    items: list[FeedItem] = field(default_factory=list)
    error: str | None = None
    response_time_ms: int | None = None
    fetched_at: datetime | None = None


async def async_fetch_feed(
    session: aiohttp.ClientSession, feed_conf: dict[str, Any]
) -> FeedFetchResult:
    """Descarga y parsea un único feed RSS/Atom/RDF."""
    feed_id = feed_conf["id"]
    url = feed_conf["url"]
    start = datetime.now(UTC)
    try:
        timeout = aiohttp.ClientTimeout(total=FEED_TIMEOUT)
        async with session.get(
            url, timeout=timeout, headers={"User-Agent": HTTP_USER_AGENT}
        ) as resp:
            resp.raise_for_status()
            raw = await resp.read()
    except Exception as err:  # noqa: BLE001 - queremos capturar cualquier fallo de red
        _LOGGER.debug("Error descargando feed %s (%s): %s", feed_id, url, err)
        return FeedFetchResult(feed_id=feed_id, ok=False, error=str(err))

    elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)

    parsed = feedparser.parse(raw)
    if parsed.bozo and not parsed.entries:
        error_msg = str(parsed.get("bozo_exception", "Formato de feed inválido"))
        _LOGGER.debug("Feed %s (%s) no pudo parsearse: %s", feed_id, url, error_msg)
        return FeedFetchResult(
            feed_id=feed_id,
            ok=False,
            error=error_msg,
            response_time_ms=elapsed_ms,
        )

    domain = urlparse(url).netloc
    source_name = feed_conf.get("name") or parsed.feed.get("title", domain)
    category = feed_conf.get("category", "")
    color = feed_conf.get("color") or None

    items: list[FeedItem] = []
    for entry in parsed.entries:
        guid = entry.get("id") or entry.get("link") or entry.get("title", "")
        title = entry.get("title", "").strip()
        description = entry.get("summary", "").strip()
        content_list = entry.get("content")
        content = content_list[0].get("value", "") if content_list else description
        link = entry.get("link", "")
        published = _parse_published(entry)

        items.append(
            FeedItem(
                guid=guid,
                title=title,
                description=description,
                content=content,
                link=link,
                published=published,
                source_id=feed_id,
                source_name=source_name,
                category=category,
                color=color,
                domain=urlparse(link).netloc if link else domain,
            )
        )

    return FeedFetchResult(
        feed_id=feed_id,
        ok=True,
        items=items,
        response_time_ms=elapsed_ms,
        fetched_at=datetime.now(UTC),
    )


def _parse_published(entry: Any) -> datetime | None:
    """Intenta extraer una fecha de publicación de una entrada de feedparser."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        struct = entry.get(key)
        if struct:
            try:
                return datetime(*struct[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                continue
    return None


def filter_and_sort_items(
    items: list[FeedItem], ticker_conf: dict[str, Any]
) -> list[FeedItem]:
    """Aplica filtros de inclusión/exclusión, deduplicación, orden y límites."""
    include_words = _split_words(ticker_conf.get("include_words"))
    exclude_words = _split_words(ticker_conf.get("exclude_words"))
    exclude_domains = _split_words(ticker_conf.get("exclude_domains"))
    exclude_categories = _split_words(ticker_conf.get("exclude_categories"))
    exclude_sources = _split_words(ticker_conf.get("exclude_sources"))

    filtered: list[FeedItem] = []
    for item in items:
        haystack = f"{item.title} {item.description}".lower()

        if include_words and not any(w in haystack for w in include_words):
            continue
        if exclude_words and any(w in haystack for w in exclude_words):
            continue
        if exclude_domains and item.domain.lower() in exclude_domains:
            continue
        if exclude_categories and item.category.lower() in exclude_categories:
            continue
        if exclude_sources and item.source_name.lower() in exclude_sources:
            continue

        filtered.append(item)

    filtered = _deduplicate(filtered, ticker_conf.get("dedup_by", DEDUP_GUID))
    filtered = _sort_items(filtered, ticker_conf.get("sort"))

    max_items = ticker_conf.get("max_items") or 0
    if max_items:
        filtered = filtered[:max_items]

    max_length = ticker_conf.get("max_length") or 0
    if max_length:
        for item in filtered:
            if len(item.title) > max_length:
                item.title = item.title[: max_length - 1].rstrip() + "…"

    return filtered


def _split_words(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [w.strip().lower() for w in raw.split(",") if w.strip()]


def _deduplicate(items: list[FeedItem], dedup_by: str) -> list[FeedItem]:
    if dedup_by == DEDUP_NONE:
        return items

    key_attr = {
        DEDUP_GUID: "guid",
        DEDUP_TITLE: "title",
        "url": "link",
    }.get(dedup_by, "guid")

    seen: set[str] = set()
    result: list[FeedItem] = []
    for item in items:
        key = getattr(item, key_attr, item.guid)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _sort_items(items: list[FeedItem], sort: str | None) -> list[FeedItem]:
    if sort == SORT_RANDOM:
        shuffled = items.copy()
        random.shuffle(shuffled)
        return shuffled

    def sort_key(item: FeedItem) -> datetime:
        return item.published or datetime.min.replace(tzinfo=UTC)

    reverse = sort != SORT_OLDEST
    return sorted(items, key=sort_key, reverse=reverse)
