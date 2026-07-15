# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

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
