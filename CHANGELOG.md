# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

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
