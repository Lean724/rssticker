# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.1] - 2026-11-07

### Corregido
- Corregidos errores de linting de Ruff (`E402`, `UP017`) en `tests/test_helpers.py` detectados por el nuevo workflow `Tests and lint` (`tests.yml`).
- Unificado `lint.yml` para validar tanto `custom_components` como `tests`.

## [1.0.0] - 2026-11-07

### Agregado
- **Sincronización dinámica de sensores**: agregar o eliminar tickers desde el Options Flow crea o remueve automáticamente las entidades `sensor` sin necesidad de recargar la integración.
- **Actualización en caliente del intervalo de polling**: cambiar `update_interval` desde Ajustes Generales actualiza inmediatamente el `DataUpdateCoordinator`.
- **Soporte de enlaces y colores por fuente en Lovelace Card**: las noticias ahora son clickeables (`open_links: true` por defecto) y respetan el color configurado en cada fuente RSS (`color`).
- **Validación de URL** en el alta y edición de fuentes RSS en el Options Flow (`http://` / `https://`).
- **Soporte de prioridad y orden de fuentes** al ordenar noticias (`priority` descendente y `order` ascendente antes de la fecha).
- `rssticker.refresh_ticker` ahora acepta tanto el `ticker_id` interno como el nombre del ticker o su `entity_id`.

### Corregido
- Actualizada la dependencia `feedparser` a `>=6.0.12` para cumplir con la validación `hassfest` de Home Assistant.
- Eliminadas las llamadas bloqueantes al sistema de archivos (`Path.exists()`, `Path.stat()`) en el event loop durante `_async_register_card`, ejecutándolas mediante `hass.async_add_executor_job`.
- Evitada la mutación in-place de objetos `FeedItem` en caché al truncar títulos con `max_length`.
- Corregida la descarga de servicios en `async_unload_entry` para que ignore banderas internas (`_card_registered`) al verificar si quedan instancias activas.
- Ajustado `hacs.json` eliminando claves obsoletas (`content_in_root`, `zip_release`) para compatibilidad estricta con las validaciones de HACS.

## [0.1.2] - 2026-07-14

### Corregido
- `TypeError: slice indices must be integers` al actualizar un ticker: los `NumberSelector` de Home Assistant devuelven `float`, y `max_items`/`max_length` se usaban directo para slicing de listas. Ahora se castean a `int` tanto al guardarlos desde el Options Flow como defensivamente en `filter_and_sort_items`. Mismo fix aplicado a `priority`/`order` de las fuentes RSS.

## [0.1.1] - 2026-07-14

### Corregido
- La Lovelace Card (`rssticker-card.js`) se movió de `www/` (raíz del repo) a `custom_components/rssticker/www/`. Al instalar vía HACS o copia manual solo se distribuye la carpeta `custom_components/rssticker`, así que la tarjeta no se estaba instalando y el registro del recurso fallaba en silencio.
- Se agregó `http` y `frontend` a las dependencias del `manifest.json` (requerido por hassfest, ya que la integración usa `hass.http` y `homeassistant.components.frontend`).
- Corregido el import de `StaticPathConfig`, que debe venir de `homeassistant.components.http` y no de `homeassistant.helpers.http`.

## [0.1.0] - 2026-07-14

### Agregado
- Integración inicial `rssticker` para Home Assistant, distribuida vía HACS.
- Config Flow para la configuración inicial (nombre, intervalo de actualización, zona horaria, idioma).
- Options Flow con administración completa de fuentes RSS (agregar, editar, eliminar, duplicar, probar) y de tickers (agregar, editar, eliminar).
- `DataUpdateCoordinator` con soporte para RSS 2.0, Atom y RDF, caché en memoria y fallback al último contenido válido ante errores.
- Filtros por palabras incluidas/excluidas, dominios, categorías y fuentes; deduplicación por GUID, título o URL; ordenamiento por más recientes, más antiguos o aleatorio.
- Sensor por cada ticker con atributos de noticias, fuentes, estado y errores.
- Servicios `rssticker.refresh`, `rssticker.refresh_ticker` y `rssticker.clear_cache`.
- Eventos `rssticker_updated` y `rssticker_error`.
- Lovelace Card (`custom:rssticker-card`) con modo individual y MultiTicker secuencial, totalmente configurable desde la UI de la tarjeta.
- Traducciones en inglés y español.
