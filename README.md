# RSS Ticker para Home Assistant

Integración nativa de Home Assistant para mostrar uno o más *News Tickers* alimentados por fuentes **RSS 2.0, Atom o RDF**, con una Lovelace Card a medida. No depende de Docker, Node.js ni servicios externos: toda la lógica corre dentro de Home Assistant.

## Características

- Configuración 100 % desde la UI (Config Flow + Options Flow), sin YAML.
- Múltiples fuentes RSS con nombre, categoría, prioridad, orden, color y estado activo/inactivo.
- Agrupá fuentes en **tickers**, cada uno con su propio título fijo, filtros, deduplicación y orden.
- Caché en memoria vía `DataUpdateCoordinator`: si un feed falla, se sigue mostrando el último contenido válido.
- Filtros de inclusión/exclusión por palabra, dominio, categoría o fuente.
- Deduplicación por GUID, título o URL.
- Servicios (`refresh`, `refresh_ticker`, `clear_cache`) y eventos (`rssticker_updated`, `rssticker_error`).
- Lovelace Card propia con modo individual y **MultiTicker** (secuencial o varias tarjetas simultáneas), con control de velocidad, dirección, tipografía, colores, separadores y más.

## Instalación

### Vía HACS (repositorio custom)

1. En HACS, andá a **Integraciones** → menú (⋮) → **Repositorios personalizados**.
2. Agregá `https://github.com/Lean724/rssticker` como tipo **Integración**.
3. Buscá "RSS Ticker" en HACS e instalalo.
4. Reiniciá Home Assistant.
5. Andá a **Ajustes → Dispositivos y servicios → Agregar integración** y buscá "RSS Ticker".

La tarjeta (`www/rssticker-card.js`) se registra automáticamente como recurso de Lovelace al iniciar la integración; no hace falta agregarla manualmente en Recursos.

### Manual

Copiá `custom_components/rssticker` a la carpeta `custom_components` de tu instalación y reiniciá Home Assistant.

## Configuración inicial

Al agregar la integración se solicita:

- **Nombre**
- **Intervalo de actualización** (1, 5, 10, 15, 30, 60 minutos o manual)
- **Zona horaria** (opcional; si se deja vacío usa la de Home Assistant)
- **Idioma** (inglés o español)

Las fuentes RSS y los tickers se agregan después, desde **Configurar** (Options Flow) → **Gestionar fuentes RSS** / **Gestionar tickers**.

### Fuentes RSS

Cada fuente tiene: nombre, URL, categoría, prioridad, orden, color opcional y estado activo. Se pueden agregar, editar, eliminar, duplicar y probar (la prueba muestra cantidad de noticias, tiempo de respuesta, última actualización y errores encontrados) directamente desde el menú de opciones.

### Tickers

Un ticker agrupa una o más fuentes RSS y define:

- Título fijo (opcional, no se desplaza).
- Contenido a mostrar (solo título / título + descripción / título + contenido).
- Ordenamiento (más recientes, más antiguos, aleatorio).
- Deduplicación (por GUID, título, URL o ninguna).
- Cantidad máxima de noticias y longitud máxima de título.
- Filtros: incluir palabras, excluir palabras, excluir dominios, excluir categorías, excluir fuentes.

Cada ticker se expone como un sensor, por ejemplo `sensor.rssticker_noticias`, con atributos `items`, `sources`, `status`, `errors` y `last_update`.

## La tarjeta Lovelace

```yaml
type: custom:rssticker-card
ticker: sensor.rssticker_noticias
mode: single
speed: 40
direction: left
pause_on_hover: true
show_source: true
show_category: false
show_description: false
show_date: false
show_time: false
separator: "  •  "
height: 40
font_size: 16
font_weight: normal
color: ""
background: ""
padding: 8
max_length: 0
```

### MultiTicker secuencial

Una sola tarjeta rota entre varios tickers, uno detrás de otro:

```yaml
type: custom:rssticker-card
mode: multi
tickers:
  - sensor.rssticker_deportes
  - sensor.rssticker_tecnologia
  - sensor.rssticker_economia
rotate_seconds: 8
```

### MultiTicker simultáneo

Agregá varias tarjetas `custom:rssticker-card` al dashboard, cada una apuntando a un `ticker` distinto (modo `single`).

## Servicios

| Servicio | Descripción |
|---|---|
| `rssticker.refresh` | Actualiza todos los feeds de una entrada (o de todas si no se especifica `config_entry_id`). |
| `rssticker.refresh_ticker` | Actualiza únicamente los feeds usados por el ticker indicado (`ticker_id`). |
| `rssticker.clear_cache` | Vacía la caché en memoria y fuerza una nueva descarga completa. |

## Eventos

- `rssticker_updated`: se emite después de actualizar cada ticker (`entry_id`, `ticker_id`, `count`).
- `rssticker_error`: se emite cuando falla la descarga de un feed (`entry_id`, `feed_id`, `feed_name`, `error`).

## Calidad y compatibilidad

- Compatible con `hassfest` y las validaciones de HACS.
- Linteado con `ruff` (ver `pyproject.toml`).
- Objetivo: alcanzar al menos nivel **Gold** en la Home Assistant Integration Quality Scale.

## Estructura del repositorio

```
rssticker/
├── custom_components/
│   └── rssticker/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── helpers.py
│       ├── const.py
│       ├── sensor.py
│       ├── services.py
│       ├── services.yaml
│       ├── translations/
│       ├── icons.json
│       ├── strings.json
│       └── www/
│           └── rssticker-card.js
├── tests/
├── .github/workflows/
├── hacs.json
├── LICENSE
├── README.md
├── CHANGELOG.md
└── pyproject.toml
```

## Licencia

MIT — ver [LICENSE](LICENSE).
