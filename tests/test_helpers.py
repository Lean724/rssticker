"""Tests unitarios para custom_components/rssticker/helpers.py.

Estos tests solo ejercitan las funciones puras (filter_and_sort_items y
utilidades relacionadas) y no requieren una instancia de Home Assistant.
"""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HELPERS_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "rssticker"
    / "helpers.py"
)
_CONST_PATH = _HELPERS_PATH.parent / "const.py"

_spec_const = importlib.util.spec_from_file_location("rssticker_const", _CONST_PATH)
_const = importlib.util.module_from_spec(_spec_const)
_spec_const.loader.exec_module(_const)

import sys
import types

for _mod_name in ("aiohttp", "feedparser"):
    if _mod_name not in sys.modules:
        try:
            __import__(_mod_name)
        except ImportError:
            stub = types.ModuleType(_mod_name)
            if _mod_name == "aiohttp":
                stub.ClientSession = object
                stub.ClientTimeout = lambda **kwargs: None
            if _mod_name == "feedparser":
                stub.parse = lambda *a, **k: None
            sys.modules[_mod_name] = stub

sys.modules.setdefault("rssticker_const", _const)

_spec_helpers = importlib.util.spec_from_file_location(
    "rssticker_helpers", _HELPERS_PATH
)
_helpers = importlib.util.module_from_spec(_spec_helpers)
# helpers.py hace `from .const import ...`, así que lo parcheamos para que
# resuelva contra el módulo const ya cargado, sin depender del paquete real.
_helpers.__dict__["__package__"] = None
sys.modules["rssticker_helpers"] = _helpers
sys.modules["const"] = _const
_source = _HELPERS_PATH.read_text(encoding="utf-8").replace(
    "from .const import", "from const import"
)
exec(compile(_source, str(_HELPERS_PATH), "exec"), _helpers.__dict__)

FeedItem = _helpers.FeedItem
filter_and_sort_items = _helpers.filter_and_sort_items


def _item(title, minutes_ago=0, guid=None, domain="example.com", category="", source="Fuente"):
    return FeedItem(
        guid=guid or title,
        title=title,
        description=f"desc {title}",
        content=f"content {title}",
        link=f"https://{domain}/{title}",
        published=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        source_id="feed1",
        source_name=source,
        category=category,
        color=None,
        domain=domain,
    )


def test_sort_newest_first():
    items = [_item("A", minutes_ago=10), _item("B", minutes_ago=1), _item("C", minutes_ago=5)]
    result = filter_and_sort_items(items, {"sort": "newest", "dedup_by": "none"})
    assert [i.title for i in result] == ["B", "C", "A"]


def test_sort_oldest_first():
    items = [_item("A", minutes_ago=10), _item("B", minutes_ago=1), _item("C", minutes_ago=5)]
    result = filter_and_sort_items(items, {"sort": "oldest", "dedup_by": "none"})
    assert [i.title for i in result] == ["A", "C", "B"]


def test_dedup_by_guid():
    items = [_item("A", guid="same"), _item("B", guid="same"), _item("C", guid="other")]
    result = filter_and_sort_items(items, {"dedup_by": "guid", "sort": "newest"})
    assert len(result) == 2


def test_include_words_filter():
    items = [_item("Gato en la ventana"), _item("Perro en el jardín")]
    result = filter_and_sort_items(
        items, {"include_words": "gato", "dedup_by": "none", "sort": "newest"}
    )
    assert len(result) == 1
    assert result[0].title == "Gato en la ventana"


def test_exclude_words_filter():
    items = [_item("Buenas noticias"), _item("Alerta de tormenta")]
    result = filter_and_sort_items(
        items, {"exclude_words": "alerta", "dedup_by": "none", "sort": "newest"}
    )
    assert len(result) == 1
    assert result[0].title == "Buenas noticias"


def test_exclude_domains_filter():
    items = [_item("A", domain="spam.com"), _item("B", domain="good.com")]
    result = filter_and_sort_items(
        items, {"exclude_domains": "spam.com", "dedup_by": "none", "sort": "newest"}
    )
    assert len(result) == 1
    assert result[0].title == "B"


def test_max_items_limit():
    items = [_item(f"Item {i}", minutes_ago=i) for i in range(10)]
    result = filter_and_sort_items(
        items, {"max_items": 3, "dedup_by": "none", "sort": "newest"}
    )
    assert len(result) == 3


def test_max_length_truncates_title():
    items = [_item("Este es un título muy largo para el ticker")]
    result = filter_and_sort_items(
        items, {"max_length": 10, "dedup_by": "none", "sort": "newest"}
    )
    assert len(result[0].title) == 10
    assert result[0].title.endswith("…")
