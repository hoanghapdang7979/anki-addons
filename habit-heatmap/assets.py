"""The page-level CSS and JS injected once into the deck-browser page. No aqt/anki
imports.

Layout is mostly inline in render.py so the blocks stay usable even if this
<style>/<script> were ever dropped; this file only holds what inline styles
cannot do (the custom tooltip, the note marker dot).

The Anki deck-browser page has no Content-Security-Policy (only the Editor page
does, see aqt/mediasrv.py), so one inline <style> and one inline <script> work.
Everything is prefixed `hh-` so it cannot touch Anki or other add-ons' elements.
"""

STYLE = """
.hh-cell { box-sizing: border-box; }
.hh-cell:hover { filter: brightness(0.92); }
.hh-note::after {
  content: ""; position: absolute; top: 1px; right: 1px; width: 3px; height: 3px;
  border-radius: 50%; background: #fff; box-shadow: 0 0 0 0.5px rgba(0, 0, 0, 0.5);
}
.hh-tip {
  position: fixed; z-index: 9999; pointer-events: none; max-width: 260px;
  padding: 6px 9px; border-radius: 4px; background: rgba(30, 30, 30, 0.95); color: #fff;
  font-size: 12px; line-height: 1.35; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  white-space: pre-wrap; word-wrap: break-word; text-align: left;
}
.hh-tip-date { font-weight: 700; }
.hh-tip-status { opacity: 0.9; }
.hh-tip-note { margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.25); }
.hh-tip-hint { margin-top: 4px; opacity: 0.6; font-size: 11px; }
""".strip()

SCRIPT = """
(function () {
  if (window.__hhInit) { return; }
  window.__hhInit = true;
  var tip = null;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text) { e.textContent = text; }
    return e;
  }

  function ensureTip() {
    if (!tip) {
      tip = el('div', 'hh-tip');
      tip.style.display = 'none';
      document.body.appendChild(tip);
    }
    return tip;
  }

  function cellOf(target) {
    return target && target.closest ? target.closest('.hh-cell') : null;
  }

  function show(cell) {
    var t = ensureTip();
    while (t.firstChild) { t.removeChild(t.firstChild); }
    t.appendChild(el('div', 'hh-tip-date', cell.getAttribute('data-label') || ''));
    t.appendChild(el('div', 'hh-tip-status', cell.getAttribute('data-status') || ''));
    var note = cell.getAttribute('data-note');
    if (note) { t.appendChild(el('div', 'hh-tip-note', note)); }
    var hint = cell.getAttribute('data-hint');
    if (hint) { t.appendChild(el('div', 'hh-tip-hint', hint)); }
    t.style.display = 'block';
    var r = cell.getBoundingClientRect();
    var gap = 8;
    var left = r.left + r.width / 2 - t.offsetWidth / 2;
    left = Math.max(4, Math.min(left, document.documentElement.clientWidth - t.offsetWidth - 4));
    var top = r.top - t.offsetHeight - gap;
    if (top < 4) { top = r.bottom + gap; }
    t.style.left = left + 'px';
    t.style.top = top + 'px';
  }

  function hide() { if (tip) { tip.style.display = 'none'; } }

  // The native title is only a no-JS fallback; drop it so two tooltips never show.
  var titled = document.querySelectorAll('.hh-cell[title]');
  for (var i = 0; i < titled.length; i++) { titled[i].removeAttribute('title'); }

  document.addEventListener('mouseover', function (e) {
    var c = cellOf(e.target);
    if (c) { c.removeAttribute('title'); show(c); }
  });
  document.addEventListener('mouseout', function (e) { if (cellOf(e.target)) { hide(); } });
  document.addEventListener('scroll', hide, true);
})();
""".strip()


def build_assets_html() -> str:
    return f"<style>{STYLE}</style><script>{SCRIPT}</script>"
