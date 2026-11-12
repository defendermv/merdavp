/* Mini runtime para a página do MerdaVP rodar como site estático (GitHub Pages).
   Reproduz o pedaço da API `dash` que a página usa: data, calc, draw, setLink.
   Carrega os arquivos de data/*.json e recarrega a cada 2 minutos. */
(function () {
  const SOURCES = { partidas: 'data/partidas.json', aram: 'data/aram.json', placar: 'data/placar.json', campeoes: 'data/campeoes.json' };
  const RELOAD_MS = 2 * 60 * 1000;
  const raw = {};      // id -> rows
  const rawText = {};  // id -> texto, para saber se mudou
  const calcs = {};    // id -> {inputs, fn}
  const memo = {};     // id -> valor calculado
  const draws = {};    // nome -> fn | {mount, update, unmount}
  const mounted = new WeakMap();
  let errors = {};

  function data(id) {
    if (calcs[id]) {
      if (id in memo) return { status: 'ok', data: memo[id] };
      const ins = calcs[id].inputs.map((i) => data(i));
      if (ins.some((x) => x.status !== 'ok')) return { status: ins.some((x) => x.status === 'error') ? 'error' : 'loading', data: null };
      try { memo[id] = calcs[id].fn(...ins.map((x) => x.data)); }
      catch (e) { console.error('cálculo', id, e); return { status: 'error', data: null, message: String(e) }; }
      return { status: 'ok', data: memo[id] };
    }
    if (errors[id]) return { status: 'error', data: [], message: errors[id] };
    if (id in raw) { const d = raw[id]; d.columns = d.length ? Object.keys(d[0]) : []; return { status: 'ok', data: d }; }
    return { status: 'loading', data: [] };
  }

  function runDraw(name) {
    const fn = draws[name];
    if (!fn) return;
    document.querySelectorAll(`[data-draw="${name}"]`).forEach((el) => {
      if (el.closest('[hidden]') && !el.hasAttribute('hidden')) return;
      try {
        if (typeof fn === 'function') fn(el);
        else {
          if (!mounted.has(el)) mounted.set(el, fn.mount ? fn.mount(el) : undefined);
          if (fn.update) fn.update(el, mounted.get(el));
        }
      } catch (e) { console.error('desenho', name, e); }
    });
  }
  function runAll() { Object.keys(draws).forEach(runDraw); }

  async function load(first) {
    let changed = false;
    await Promise.all(Object.entries(SOURCES).map(async ([id, url]) => {
      try {
        const r = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const txt = await r.text();
        if (txt !== rawText[id]) { rawText[id] = txt; raw[id] = JSON.parse(txt); changed = true; }
        delete errors[id];
      } catch (e) { if (first) { errors[id] = String(e); changed = true; } console.warn('carregar', id, e); }
    }));
    if (changed) { for (const k of Object.keys(memo)) delete memo[k]; runAll(); }
  }

  window.dash = {
    data,
    calc(id, o) { calcs[id] = { inputs: o.inputs || [], fn: o.fn }; },
    loader() {},
    draw(name, fn) { if (fn) draws[name] = fn; else runDraw(name); },
    setLink(name) { try { history.replaceState(null, '', '#' + name); } catch (e) { /* ignora */ } },
    params() { return {}; }, setParams() {}, resetParams() {},
    refresh() { load(false); },
    onData(fn) { fn(); },
    colors: ['#3ea2e6', '#e8594f', '#3ccf8e', '#e9b949', '#b48cf2'],
  };

  document.addEventListener('DOMContentLoaded', () => {
    runAll();
    load(true);
    setInterval(() => { if (!document.hidden) load(false); }, RELOAD_MS);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) load(false); });
  });
})();
