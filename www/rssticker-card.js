/**
 * RSS Ticker Card
 * Custom Lovelace card para la integración RSS Ticker de Home Assistant.
 *
 * Responsabilidad exclusiva: renderizar el/los ticker(s) y aplicar la
 * configuración visual (velocidad, tipografía, colores, MultiTicker, etc.).
 * Toda la descarga, parseo, filtrado, deduplicación y caché de los feeds
 * ocurre del lado de la integración (custom_components/rssticker).
 *
 * Implementada como HTMLElement estándar (sin depender de clases internas
 * de Home Assistant) para máxima compatibilidad entre versiones.
 */

class RssTickerCard extends HTMLElement {
  static getStubConfig() {
    return {
      type: "custom:rssticker-card",
      ticker: "",
      mode: "single",
      speed: 40,
      direction: "left",
      pause_on_hover: true,
      content: "title_description",
      show_date: false,
      show_time: false,
      show_source: true,
      show_category: false,
      show_description: false,
      separator: "  •  ",
      height: 40,
      font_size: 16,
      font_weight: "normal",
      color: "",
      background: "",
      padding: 8,
      rotate_seconds: 8,
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Falta la configuración de la tarjeta");
    }
    if (!config.ticker && !(config.tickers && config.tickers.length)) {
      throw new Error(
        "Debés especificar 'ticker' (entidad o nombre de ticker) o 'tickers' (lista) en la configuración"
      );
    }

    this._config = {
      mode: "single",
      speed: 40,
      direction: "left",
      pause_on_hover: true,
      content: "title_description",
      show_title: true,
      show_date: false,
      show_time: false,
      show_source: true,
      show_category: false,
      show_description: false,
      separator: "  •  ",
      height: 40,
      font_size: 16,
      font_weight: "normal",
      width: "100%",
      color: "",
      background: "",
      padding: 8,
      max_length: 0,
      rotate_seconds: 8,
      ...config,
    };

    this._currentIndex = 0;
    this._lastRenderedText = null;

    if (!this._hasRenderedShell) {
      this._buildShell();
    }
    this._applyStaticStyles();
    this._restartRotationTimer();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  get hass() {
    return this._hass;
  }

  getCardSize() {
    return 1;
  }

  connectedCallback() {
    this._restartRotationTimer();
  }

  disconnectedCallback() {
    if (this._rotationTimer) {
      clearInterval(this._rotationTimer);
      this._rotationTimer = null;
    }
  }

  _restartRotationTimer() {
    if (this._rotationTimer) {
      clearInterval(this._rotationTimer);
      this._rotationTimer = null;
    }
    if (this._config && this._config.mode === "multi") {
      this._rotationTimer = setInterval(() => {
        const total = this._tickerRefs().length;
        if (total > 0) {
          this._currentIndex = (this._currentIndex + 1) % total;
          this._update(true);
        }
      }, (this._config.rotate_seconds || 8) * 1000);
    }
  }

  _buildShell() {
    const root = this.attachShadow ? this.attachShadow({ mode: "open" }) : this;
    root.innerHTML = `
      <style>
        ha-card, .rssticker-card {
          overflow: hidden;
        }
        .rssticker-empty {
          display: block;
          padding: 12px;
          color: var(--secondary-text-color);
          font-style: italic;
        }
        .rssticker-fixed-title {
          white-space: nowrap;
        }
        .rssticker-viewport {
          box-sizing: border-box;
        }
        .rssticker-track {
          display: inline-flex;
          white-space: nowrap;
          gap: 3em;
          animation-name: rssticker-scroll;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
        }
        .rssticker-track.reverse {
          animation-direction: reverse;
        }
        .pause-on-hover:hover .rssticker-track {
          animation-play-state: paused;
        }
        @keyframes rssticker-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      </style>
      <ha-card class="rssticker-card">
        <div class="rssticker-fixed-title" part="title"></div>
        <div class="rssticker-viewport">
          <div class="rssticker-track">
            <span class="rssticker-content"></span>
            <span class="rssticker-content" aria-hidden="true"></span>
          </div>
        </div>
        <div class="rssticker-empty" style="display:none;"></div>
      </ha-card>
    `;
    this._root = root;
    this._hasRenderedShell = true;
  }

  _applyStaticStyles() {
    const cfg = this._config;
    const card = this._root.querySelector(".rssticker-card");
    const titleEl = this._root.querySelector(".rssticker-fixed-title");
    const viewport = this._root.querySelector(".rssticker-viewport");
    const track = this._root.querySelector(".rssticker-track");

    card.classList.toggle("pause-on-hover", !!cfg.pause_on_hover);

    titleEl.style.fontSize = `${cfg.font_size}px`;
    titleEl.style.fontWeight = "bold";
    titleEl.style.color = cfg.color || "var(--primary-text-color)";
    titleEl.style.background = cfg.background || "var(--secondary-background-color)";
    titleEl.style.padding = `4px ${cfg.padding}px`;

    viewport.style.height = `${cfg.height}px`;
    viewport.style.width = cfg.width;
    viewport.style.padding = `0 ${cfg.padding}px`;
    viewport.style.background = cfg.background || "var(--card-background-color)";
    viewport.style.overflow = "hidden";
    viewport.style.position = "relative";
    viewport.style.display = "flex";
    viewport.style.alignItems = "center";

    track.classList.toggle("reverse", cfg.direction === "right");
    track.style.fontSize = `${cfg.font_size}px`;
    track.style.fontWeight = cfg.font_weight;
    track.style.color = cfg.color || "var(--primary-text-color)";
  }

  _tickerRefs() {
    const cfg = this._config;
    if (cfg.tickers && cfg.tickers.length) return cfg.tickers;
    if (cfg.ticker) return [cfg.ticker];
    return [];
  }

  _resolveEntityId(idOrName) {
    if (!this._hass) return null;
    if (this._hass.states[idOrName]) return idOrName;
    const needle = String(idOrName).toLowerCase();
    const match = Object.keys(this._hass.states).find(
      (eid) =>
        eid.startsWith("sensor.") &&
        eid.includes("rssticker") &&
        (this._hass.states[eid].attributes.friendly_name || "")
          .toLowerCase()
          .includes(needle)
    );
    return match || null;
  }

  _activeEntityId() {
    const refs = this._tickerRefs();
    if (!refs.length) return null;
    if (this._config.mode === "multi") {
      return this._resolveEntityId(refs[this._currentIndex % refs.length]);
    }
    return this._resolveEntityId(refs[0]);
  }

  _formatItem(item) {
    const cfg = this._config;
    const parts = [];
    const lang = (this._hass && this._hass.locale && this._hass.locale.language) || "es";

    if (cfg.show_date || cfg.show_time) {
      const d = item.published ? new Date(item.published) : null;
      if (d && !isNaN(d)) {
        const dateStr = cfg.show_date ? d.toLocaleDateString(lang) : "";
        const timeStr = cfg.show_time
          ? d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" })
          : "";
        const stamp = [dateStr, timeStr].filter(Boolean).join(" ");
        if (stamp) parts.push(stamp);
      }
    }

    if (cfg.show_category && item.category) {
      parts.push(`[${item.category}]`);
    }

    let title = item.title || "";
    if (cfg.max_length && title.length > cfg.max_length) {
      title = title.slice(0, cfg.max_length - 1).trimEnd() + "…";
    }
    parts.push(title);

    if (cfg.show_description && item.description) {
      parts.push(`— ${item.description}`);
    } else if (cfg.content === "title_content" && item.content) {
      parts.push(`— ${item.content}`);
    }

    if (cfg.show_source && item.source) {
      parts.push(`(${item.source})`);
    }

    return parts.join(" ");
  }

  _update(force) {
    if (!this._hass || !this._config || !this._root) return;

    const emptyEl = this._root.querySelector(".rssticker-empty");
    const titleEl = this._root.querySelector(".rssticker-fixed-title");
    const viewport = this._root.querySelector(".rssticker-viewport");
    const track = this._root.querySelector(".rssticker-track");
    const contentSpans = this._root.querySelectorAll(".rssticker-content");

    const entityId = this._activeEntityId();
    const stateObj = entityId ? this._hass.states[entityId] : null;

    if (!stateObj) {
      viewport.style.display = "none";
      titleEl.style.display = "none";
      emptyEl.style.display = "block";
      emptyEl.textContent = entityId
        ? `Entidad no encontrada: ${entityId}`
        : "Configurá un ticker válido";
      return;
    }

    const items = stateObj.attributes.items || [];
    if (!items.length) {
      viewport.style.display = "none";
      titleEl.style.display = "none";
      emptyEl.style.display = "block";
      emptyEl.textContent = "Sin noticias disponibles";
      return;
    }

    emptyEl.style.display = "none";
    viewport.style.display = "flex";

    const title = this._config.show_title !== false ? stateObj.attributes.title : "";
    if (title) {
      titleEl.style.display = "block";
      titleEl.textContent = title;
    } else {
      titleEl.style.display = "none";
    }

    const sep = this._config.separator ?? "  •  ";
    const text = items.map((i) => this._formatItem(i)).join(sep);

    if (text !== this._lastRenderedText || force) {
      this._lastRenderedText = text;
      contentSpans.forEach((span) => (span.textContent = text));

      const duration = Math.max(5, (text.length || 1) / (this._config.speed / 10));
      track.style.animationDuration = `${duration}s`;
      // Reinicia la animación para evitar saltos al cambiar de contenido
      track.style.animationName = "none";
      // eslint-disable-next-line no-unused-expressions
      track.offsetHeight;
      track.style.animationName = "rssticker-scroll";
    }
  }
}

customElements.define("rssticker-card", RssTickerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "rssticker-card",
  name: "RSS Ticker Card",
  description:
    "Muestra un ticker de noticias alimentado por la integración RSS Ticker (modo individual o MultiTicker).",
  preview: false,
});
