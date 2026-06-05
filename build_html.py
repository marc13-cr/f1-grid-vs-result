#!/usr/bin/env python3
"""
build_html.py — Genera dashboard.html autocontenido (scroll narrativo).
"""
import json, os
import pandas as pd
from scipy import stats as sc

BASE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")

# ── Datos ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(DATA_DIR, "f1_positions_base.csv"))
for c in ["grid_position", "final_position", "points", "laps", "positions_gained"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["season"]   = df["season"].astype(str)
df["driver"]   = df["givenName"].fillna("") + " " + df["familyName"].fillna("")
df["finished"] = df["status"] == "Finished"
df = df[df["grid_position"] > 0].copy()

COLS = ["season", "round", "raceName", "circuitName", "country",
        "driver", "code", "constructorName",
        "grid_position", "final_position", "positions_gained",
        "status", "finished"]

df_clean = df[COLS].dropna(subset=["grid_position", "final_position"]).copy()
df_clean["grid_position"]    = df_clean["grid_position"].astype(int)
df_clean["final_position"]   = df_clean["final_position"].astype(int)
df_clean["positions_gained"] = df_clean["positions_gained"].fillna(0).astype(int)
df_clean["finished"]         = df_clean["finished"].astype(bool)

seasons  = sorted(df_clean["season"].unique().tolist())
circuits = sorted(df_clean["circuitName"].unique().tolist())

DATA_JSON     = df_clean.to_json(orient="records", force_ascii=False)
SEASONS_JSON  = json.dumps(seasons)
CIRCUITS_JSON = json.dumps(circuits)

# ── Datos meteorológicos ───────────────────────────────────────────────────────
weather = pd.read_csv(os.path.join(DATA_DIR, "weather_base.csv"))
weather["season"] = weather["season"].astype(str)
weather["round"]  = weather["round"].astype(str)
for c in ["precipitation_mm", "temp_max_c", "wind_max_kmh"]:
    weather[c] = pd.to_numeric(weather[c], errors="coerce")

# Movilidad media por carrera (avg posiciones ganadas en valor absoluto)
_pos = df_clean.copy()
_pos["round"] = _pos["round"].astype(str)
_pos["abs_gained"] = _pos["positions_gained"].abs()
_race_stats = _pos.groupby(["season", "round"]).agg(
    avg_abs_gained=("abs_gained",         "mean"),
    avg_gained    =("positions_gained",   "mean"),
    pct_improved  =("positions_gained",   lambda x: (x > 0).mean() * 100),
    n_drivers     =("driver",             "count"),
).reset_index().round(3)

_wm = weather.merge(_race_stats, on=["season", "round"], how="inner")
_wm["is_wet"] = (_wm["precipitation_mm"] >= 2.0)

# Top 5 carreras más lluviosas (para anotaciones)
_top_wet = _wm.nlargest(5, "precipitation_mm")[["raceName","season","precipitation_mm"]].values.tolist()
TOP_WET_JSON = json.dumps(_top_wet)

WEATHER_JSON = _wm[[
    "season","round","raceName","circuitName","date",
    "precipitation_mm","temp_max_c","wind_max_kmh","is_wet",
    "avg_abs_gained","avg_gained","pct_improved","n_drivers"
]].to_json(orient="records", force_ascii=False)

# Media movilidad: seca vs lluviosa
_dry = _wm[~_wm["is_wet"]]["avg_abs_gained"].mean()
_wet = _wm[_wm["is_wet"]]["avg_abs_gained"].mean()
WET_LIFT_PCT = f"{(_wet/_dry - 1)*100:.0f}" if _dry else "—"
N_WET_RACES  = str(_wm["is_wet"].sum())

# ── Estadísticas para las conclusiones ────────────────────────────────────────
def safe_r(g):
    if len(g) < 5: return float("nan")
    r, _ = sc.spearmanr(g["grid_position"], g["final_position"])
    return r

_sp = df_clean.dropna(subset=["grid_position", "final_position"])
_cr = _sp.groupby("circuitName")[["grid_position","final_position"]].apply(safe_r).dropna()
_sr = _sp.groupby("season")[["grid_position","final_position"]].apply(safe_r).dropna().sort_index()
_global_r, _ = sc.spearmanr(_sp["grid_position"], _sp["final_position"])

GLOBAL_R       = f"{_global_r:.2f}"
MOST_RIGID     = _cr.idxmax()
MOST_RIGID_R   = f"{_cr.max():.2f}"
MOST_DYNAMIC   = _cr.idxmin()
MOST_DYNAMIC_R = f"{_cr.min():.2f}"
RIGID_SEASON   = _sr.idxmax()
RIGID_SEASON_R = f"{_sr.max():.2f}"
OPEN_SEASON    = _sr.idxmin()
OPEN_SEASON_R  = f"{_sr.min():.2f}"
PCT_IMPROVED   = f"{(_sp['positions_gained'] > 0).mean() * 100:.0f}"
N_RACES        = str(len(_sp.groupby(['season','round'])))

# ── Bloques HTML ───────────────────────────────────────────────────────────────
SEASON_BTNS = "\n            ".join(
    f'<button class="sbtn active" data-s="{s}">{s}</button>'
    for s in seasons
)
CIRCUIT_OPTS = "\n            ".join(
    ['<option value="">Todos los circuitos</option>'] +
    [f'<option value="{c}">{c}</option>' for c in circuits]
)

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }
body {
  background: #111;
  color: #f0f0f0;
  font-family: 'Inter', 'Helvetica Neue', sans-serif;
  font-size: 15px;
  line-height: 1.5;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }

/* ── header ── */
#header {
  position: sticky; top: 0; z-index: 200;
  background: #191919;
  border-bottom: 3px solid #e10600;
  padding: 10px 28px;
  display: flex; align-items: center; gap: 24px; flex-wrap: wrap;
  box-shadow: 0 2px 16px rgba(0,0,0,.6);
}
#header h1 { font-size: 1rem; font-weight: 800; white-space: nowrap; }
#header h1 span { color: #e10600; }
.subtitle  { font-size: .65rem; color: #666; margin-top: 1px; }

.filters { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; margin-left: auto; }
.fg      { display: flex; flex-direction: column; gap: 5px; }
.flabel  { font-size: .6rem; color: #666; letter-spacing: .07em; font-weight: 600;
           text-transform: uppercase; }

/* season pills */
.srow { display: flex; gap: 5px; }
.sbtn {
  background: #2a2a2a; border: 1.5px solid #3a3a3a;
  color: #777; padding: 4px 12px;
  border-radius: 20px; cursor: pointer;
  font-size: .74rem; font-family: inherit; font-weight: 600;
  transition: all .15s;
}
.sbtn.active  { background: #e10600; border-color: #e10600; color: #fff; }
.sbtn:hover:not(.active) { background: #333; color: #ddd; border-color: #555; }

/* circuit select */
select {
  background: #252525; border: 1.5px solid #3a3a3a;
  color: #e8e8e8; padding: 5px 10px;
  border-radius: 6px; font-size: .78rem; font-family: inherit;
  cursor: pointer; outline: none; min-width: 210px;
  transition: border-color .15s;
}
select:hover  { border-color: #666; }
select:focus  { border-color: #e10600; }
select option { background: #252525; }

/* checkbox */
.chkrow { display: flex; align-items: center; gap: 7px;
          font-size: .74rem; color: #999; cursor: pointer; }
input[type=checkbox] { accent-color: #e10600; width: 15px; height: 15px; cursor: pointer; }

/* ── main scroll container ── */
#main { max-width: 1160px; margin: 0 auto; padding: 0 28px 60px; }

/* ── section ── */
.section { padding-top: 52px; }
.sec-hdr { margin-bottom: 14px; }
.sec-num {
  display: inline-block;
  font-size: .65rem; font-weight: 700; letter-spacing: .1em;
  color: #e10600; text-transform: uppercase; margin-bottom: 6px;
}
.sec-title {
  font-size: 1.18rem; font-weight: 700; color: #f4f4f4;
  line-height: 1.3; margin-bottom: 8px;
}
.sec-desc {
  font-size: .82rem; color: #888; line-height: 1.7; max-width: 860px;
}

/* ── KPI row ── */
.kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  margin-top: 20px;
}
.kpi-card {
  background: #1c1c1c; border: 1px solid #2d2d2d; border-radius: 10px;
  padding: 14px 18px;
}
.kpi-label { font-size: .68rem; color: #666; letter-spacing: .05em;
             text-transform: uppercase; margin-bottom: 6px; }
.kpi-val   { font-size: 1.5rem; font-weight: 800; line-height: 1.1; color: #f0f0f0; }
.kpi-val.red  { color: #e10600; }
.kpi-val.teal { color: #00c9a7; }

/* ── chart card ── */
.chart-card {
  background: #1a1a1a; border: 1px solid #272727; border-radius: 10px;
  overflow: hidden; margin-top: 10px;
}
.card-note {
  font-size: .74rem; color: #666; padding: 8px 16px 12px;
  border-top: 1px solid #222; line-height: 1.6;
}

/* ── divider ── */
.divider {
  border: none; border-top: 1px solid #252525;
  margin: 56px 0 0;
}

/* ── footer ── */
.footer {
  text-align: center; padding: 28px 0 8px;
  font-size: .65rem; color: #444;
}

/* ── badge circuito activo ── */
#badge-bar {
  display: none;
  align-items: center; gap: 10px;
  margin-top: 14px;
  padding: 8px 14px;
  background: rgba(225,6,0,0.10);
  border: 1.5px solid rgba(225,6,0,0.35);
  border-radius: 8px;
  font-size: .8rem; color: #f0f0f0;
}
#badge-bar strong { color: #e10600; }
.badge-x {
  margin-left: auto;
  background: none; border: none; cursor: pointer;
  color: #888; font-size: 1rem; line-height: 1;
  padding: 0 2px; transition: color .15s;
}
.badge-x:hover { color: #e10600; }

/* ── estado vacío ── */
.empty-msg {
  display: flex; align-items: center; justify-content: center;
  height: 100%; min-height: 160px;
  font-size: .9rem; color: #444;
  font-style: italic;
}

/* ── conclusiones ── */
.concl-grid {
  display: grid; grid-template-columns: repeat(4,1fr); gap: 12px;
  margin-top: 20px; margin-bottom: 24px;
}
.concl-card {
  background: #1c1c1c; border: 1px solid #2d2d2d; border-radius: 10px;
  padding: 16px 18px;
}
.concl-val {
  font-size: 1.55rem; font-weight: 800; line-height: 1.1;
  margin-bottom: 6px; color: #f0f0f0;
}
.concl-lbl {
  font-size: .72rem; color: #aaa; font-weight: 600;
  letter-spacing: .03em; margin-bottom: 4px;
}
.concl-sub { font-size: .66rem; color: #555; }

.hyp-list { display: flex; flex-direction: column; gap: 12px; }
.hyp-row {
  display: flex; align-items: baseline; gap: 12px;
  background: #181818; border: 1px solid #252525;
  border-radius: 8px; padding: 12px 16px;
}
.hyp-tag {
  font-size: .65rem; font-weight: 700; letter-spacing: .06em;
  padding: 3px 9px; border-radius: 20px; white-space: nowrap;
  text-transform: uppercase;
}
.hyp-tag.yes  { background: rgba(0,201,167,.15); color: #00c9a7;
                border: 1px solid rgba(0,201,167,.3); }
.hyp-tag.part { background: rgba(255,140,0,.12); color: #ff8c00;
                border: 1px solid rgba(255,140,0,.3); }
.hyp-p { font-size: .8rem; color: #bbb; line-height: 1.6; }
"""

# ── JavaScript ─────────────────────────────────────────────────────────────────
JS = r"""
const RAW      = __DATA_JSON__;
const SEASONS  = __SEASONS_JSON__;
const CIRCUITS = __CIRCUITS_JSON__;

let selSeasons = new Set(SEASONS);
let selCircuit = null;
let finOnly    = false;
let rigInit    = false;

// ── filtros ───────────────────────────────────────────────────────────────────
function getFilt() {
  return RAW.filter(d =>
    selSeasons.has(d.season) &&
    (!selCircuit || d.circuitName === selCircuit) &&
    (!finOnly || d.finished) &&
    d.grid_position != null && d.final_position != null
  );
}
function getAllSeas() {
  return RAW.filter(d =>
    selSeasons.has(d.season) &&
    (!finOnly || d.finished) &&
    d.grid_position != null && d.final_position != null
  );
}

// ── estadísticas ──────────────────────────────────────────────────────────────
function rankArr(arr) {
  const n = arr.length;
  const idx = arr.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
  const r = new Array(n);
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n && idx[j][0] === idx[i][0]) j++;
    const avg = (i + j - 1) / 2 + 1;
    for (let k = i; k < j; k++) r[idx[k][1]] = avg;
    i = j;
  }
  return r;
}

function spearman(arr) {
  if (arr.length < 5) return null;
  const n  = arr.length;
  const x  = arr.map(d => d.grid_position);
  const y  = arr.map(d => d.final_position);
  const rx = rankArr(x), ry = rankArr(y);
  let d2 = 0;
  for (let i = 0; i < n; i++) d2 += (rx[i] - ry[i]) ** 2;
  return 1 - 6 * d2 / (n * (n * n - 1));
}

function linreg(arr) {
  const n = arr.length;
  if (n < 2) return null;
  const x  = arr.map(d => d.grid_position);
  const y  = arr.map(d => d.final_position);
  const mx = x.reduce((a, b) => a + b) / n;
  const my = y.reduce((a, b) => a + b) / n;
  const num = x.reduce((a, xi, i) => a + (xi - mx) * (y[i] - my), 0);
  const den = x.reduce((a, xi) => a + (xi - mx) ** 2, 0);
  if (!den) return null;
  const m = num / den;
  return { m, b: my - m * mx };
}

function groupBy(arr, key) {
  const g = {};
  arr.forEach(d => { (g[d[key]] = g[d[key]] || []).push(d); });
  return g;
}

function groupSpearman(arr, key) {
  return Object.entries(groupBy(arr, key))
    .map(([k, a]) => ({ key: k, r: spearman(a), n: a.length }))
    .filter(d => d.r !== null);
}

// ── paleta y layout base ──────────────────────────────────────────────────────
const C = {
  red:'#e10600', teal:'#00c9a7', dark:'#111', card:'#1a1a1a',
  text:'#eeeeee', muted:'#999999', faint:'#555555', grid:'#272727'
};

function BL(extra) {
  return Object.assign({
    paper_bgcolor: C.card,
    plot_bgcolor:  '#161616',
    font: { color: C.text, family:"'Inter','Helvetica Neue',sans-serif", size: 12 },
    margin: { l: 20, r: 20, t: 36, b: 48 },
    xaxis: {
      gridcolor: C.grid, linecolor: '#333', zerolinecolor: '#333',
      tickfont:  { size: 12, color: '#aaa' },
      title:     { font: { size: 13, color: '#ccc' } }
    },
    yaxis: {
      gridcolor: C.grid, linecolor: '#333', zerolinecolor: '#333',
      tickfont:  { size: 12, color: '#aaa' },
      title:     { font: { size: 13, color: '#ccc' } }
    },
    legend:     { bgcolor: 'rgba(0,0,0,0)', font: { size: 12, color: C.text } },
    hoverlabel: { bgcolor: '#222', font: { size: 12, color: C.text }, bordercolor: '#444' },
    modebar:    { bgcolor: C.card, color: '#888', activecolor: C.red }
  }, extra || {});
}

const PLOTCFG = {
  responsive: true, displaylogo: false,
  modeBarButtonsToRemove: ['select2d','lasso2d','autoScale2d','toImage']
};

// ── KPIs ──────────────────────────────────────────────────────────────────────
function renderKPIs(filt) {
  const r   = spearman(filt);
  const all = getAllSeas();
  const pg  = filt.filter(d => d.positions_gained !== undefined);
  const pct = pg.length ? pg.filter(d => d.positions_gained > 0).length / pg.length * 100 : null;
  const cr  = groupSpearman(all, 'circuitName');

  document.getElementById('kpi-r').textContent   = r   !== null ? r.toFixed(2)        : '—';
  document.getElementById('kpi-pct').textContent = pct !== null ? `${Math.round(pct)}%` : '—';

  if (cr.length) {
    cr.sort((a, b) => b.r - a.r);
    document.getElementById('kpi-rigid').textContent   = cr[0].key;
    document.getElementById('kpi-dynamic').textContent = cr[cr.length - 1].key;
  }
}

// ── GRÁFICO 01: línea agregada (global) / scatter (circuito) ──────────────────
function renderScatter(filt) {
  if (!filt.length) { emptyFig('fig-scatter'); return; }

  const traces = [];

  if (!selCircuit) {
    // ── Vista global: posición final media por posición de salida ──────────────
    const byGrid = {};
    filt.forEach(d => {
      const g = d.grid_position;
      (byGrid[g] = byGrid[g] || []).push(d);
    });

    const slots = Array.from({length: 20}, (_, i) => i + 1)
                       .filter(g => byGrid[g] && byGrid[g].length >= 3);

    const means = slots.map(g => {
      const v = byGrid[g].map(d => d.final_position);
      return v.reduce((a, b) => a + b) / v.length;
    });
    const stds = slots.map((g, i) => {
      const v = byGrid[g].map(d => d.final_position);
      const m = means[i];
      return Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / v.length);
    });
    const ns          = slots.map(g => byGrid[g].length);
    const pctImproved = slots.map(g =>
      (byGrid[g].filter(d => d.positions_gained > 0).length / byGrid[g].length * 100).toFixed(0)
    );
    const pctWin = slots.map(g =>
      (byGrid[g].filter(d => d.final_position === 1).length / byGrid[g].length * 100).toFixed(1)
    );

    // Banda de ±1 desviación estándar
    traces.push({
      x: slots, y: means.map((m, i) => Math.min(20, +(m + stds[i]).toFixed(1))),
      mode: 'lines', type: 'scatter', line: { width: 0 },
      showlegend: false, hoverinfo: 'skip', name: 'upper'
    });
    traces.push({
      x: slots, y: means.map((m, i) => Math.max(1, +(m - stds[i]).toFixed(1))),
      mode: 'lines', type: 'scatter',
      fill: 'tonexty', fillcolor: 'rgba(225,6,0,0.10)',
      line: { width: 0 }, showlegend: false, hoverinfo: 'skip', name: 'lower'
    });

    // Línea de media
    traces.push({
      x: slots, y: means.map(m => +m.toFixed(2)),
      mode: 'lines+markers', type: 'scatter',
      name: 'Posición final media',
      line:   { color: C.red, width: 2.5 },
      marker: { size: 9, color: C.card, symbol: 'circle',
                line: { color: C.red, width: 2.5 } },
      customdata: slots.map((g, i) => [
        g, means[i].toFixed(1), stds[i].toFixed(1),
        ns[i], pctImproved[i], pctWin[i]
      ]),
      hovertemplate:
        'Salida desde <b>P%{customdata[0]}</b><br>' +
        'Posición final media: <b>P%{customdata[1]}</b>  (±%{customdata[2]})<br>' +
        '%{customdata[3]} participaciones analizadas<br>' +
        '%{customdata[4]}% terminan mejor que su posición de salida<br>' +
        '%{customdata[5]}% consiguen la victoria' +
        '<extra></extra>'
    });

    // Diagonal de referencia (grid = resultado)
    traces.push({
      x: [1, 20], y: [1, 20], mode: 'lines', type: 'scatter', hoverinfo: 'skip',
      name: 'Sin cambio de posición (referencia)',
      line: { color: '#444', width: 1.5, dash: 'dot' }
    });

    Plotly.react('fig-scatter', traces, BL({
      title:  { text: 'Posición final media según la posición de salida',
                font: { size: 13 }, x: 0.01, xanchor: 'left' },
      margin: { l: 62, r: 24, t: 50, b: 62 },
      xaxis: {
        title:    { text: 'Posición de salida (parrilla)', font: { size: 13, color: '#ccc' } },
        range:    [0.5, 20.5], dtick: 1,
        gridcolor: '#1a1a1a', linecolor: '#333',
        tickfont: { size: 11, color: '#999' }
      },
      yaxis: {
        title:    { text: 'Posición final media', font: { size: 13, color: '#ccc' } },
        range:    [0.5, 20.5], dtick: 2, autorange: 'reversed',
        gridcolor: '#1a1a1a', linecolor: '#333',
        tickfont: { size: 12, color: '#999' }
      },
      legend: { orientation: 'h', x: 0.5, y: -0.14,
                xanchor: 'center', yanchor: 'top', font: { size: 11 } }
    }), PLOTCFG);

  } else {
    // ── Vista por circuito: scatter individual ─────────────────────────────────
    const pg   = filt.map(d => d.positions_gained || 0);
    const vmax = Math.max(Math.abs(Math.min(...pg, 0)), Math.abs(Math.max(...pg, 0)), 1);
    const r    = spearman(filt);
    const reg  = linreg(filt);

    // Etiqueta visible: código de 3 letras; si no existe, 3 letras del apellido
    const labels = filt.map(d => {
      if (d.code && d.code !== 'null' && d.code !== '') return d.code;
      const parts = (d.driver || '').split(' ');
      return parts[parts.length - 1].slice(0, 3).toUpperCase();
    });

    traces.push({
      x: filt.map(d => d.grid_position),
      y: filt.map(d => d.final_position),
      mode: 'markers+text',
      type: 'scatter',
      name: '',
      text:         labels,
      textposition: 'top center',
      textfont:     { size: 8.5, color: 'rgba(220,220,220,0.75)',
                      family: "'Inter',sans-serif" },
      marker: {
        color: pg,
        colorscale: [[0, C.red], [0.5, '#555'], [1, C.teal]],
        cmin: -vmax, cmax: vmax,
        size: 8, opacity: 0.85, line: { width: 0 },
        colorbar: {
          title:    { text: 'Pos.<br>ganadas', font: { size: 11, color: '#ccc' } },
          thickness: 12, len: 0.65,
          tickfont: { size: 11, color: '#bbb' }, x: 1.01
        }
      },
      customdata: filt.map(d => [
        d.driver, d.raceName, d.season,
        (d.positions_gained >= 0 ? '+' : '') + d.positions_gained,
        d.constructorName
      ]),
      hovertemplate:
        '<b>%{customdata[0]}</b>  ·  %{customdata[4]}<br>' +
        '%{customdata[1]}  %{customdata[2]}<br>' +
        'Salió <b>P%{x}</b>  →  Llegó <b>P%{y}</b>  (%{customdata[3]} posiciones)' +
        '<extra></extra>'
    });

    if (reg) {
      traces.push({
        x: [1, 20],
        y: [Math.max(1, Math.min(20, reg.m + reg.b)),
            Math.max(1, Math.min(20, 20 * reg.m + reg.b))],
        mode: 'lines', type: 'scatter', hoverinfo: 'skip',
        name: r !== null ? `Regresión  r = ${r.toFixed(2)}` : 'Regresión',
        line: { color: C.red, width: 2, dash: 'dash' }
      });
    }
    traces.push({
      x: [1, 20], y: [1, 20], mode: 'lines', type: 'scatter', hoverinfo: 'skip',
      name: 'Sin cambio de posición',
      line: { color: '#444', width: 1.5, dash: 'dot' }
    });

    Plotly.react('fig-scatter', traces, BL({
      title:  { text: `Parrilla vs. Resultado  ·  ${selCircuit}`,
                font: { size: 13 }, x: 0.01, xanchor: 'left' },
      margin: { l: 62, r: 30, t: 50, b: 62 },
      xaxis: {
        title:    { text: 'Posición de salida (parrilla)', font: { size: 13, color: '#ccc' } },
        range:    [0.5, 20.5], dtick: 2,
        gridcolor: '#1a1a1a', linecolor: '#333',
        tickfont: { size: 12, color: '#999' }
      },
      yaxis: {
        title:    { text: 'Posición final', font: { size: 13, color: '#ccc' } },
        range:    [0.5, 20.5], dtick: 2,
        gridcolor: '#1a1a1a', linecolor: '#333',
        tickfont: { size: 12, color: '#999' }
      }
    }), PLOTCFG);
  }
}

// ── RIGIDEZ ───────────────────────────────────────────────────────────────────
function renderRigidez(all) {
  if (!all.length) { emptyFig('fig-rigidez'); return; }
  const cr = groupSpearman(all, 'circuitName').sort((a, b) => a.r - b.r);

  Plotly.react('fig-rigidez', [{
    x: cr.map(d => d.r),
    y: cr.map(d => d.key),
    orientation: 'h', type: 'bar',
    marker: {
      color: cr.map(d => d.key === selCircuit ? C.red : '#4a4a4a'),
      line:  { color: cr.map(d => d.key === selCircuit ? '#ff4040' : '#666'), width: 1 }
    },
    text:          cr.map(d => d.r.toFixed(2)),
    textposition:  'outside',
    textfont:      { color: '#ccc', size: 11, family: "'Inter',sans-serif" },
    customdata:    cr.map(d => [d.n, d.key]),
    hovertemplate: '<b>%{customdata[1]}</b><br>Spearman r: <b>%{x:.3f}</b><br>N observaciones: %{customdata[0]}<extra></extra>'
  }], BL({
    showlegend: false,
    clickmode: 'event',
    margin: { l: 192, r: 50, t: 18, b: 48 },
    xaxis: {
      title: { text: 'Spearman r  (más rígido →)', font: { size: 13, color: '#ccc' } },
      range: [0, 1.2],
      gridcolor: '#1f1f1f', linecolor: '#333', zerolinecolor: '#333',
      tickfont: { size: 12, color: '#999' }
    },
    yaxis: {
      gridcolor: 'rgba(0,0,0,0)', linecolor: '#333',
      tickfont: { size: 10.5, color: '#ddd' },
      automargin: true
    }
  }), PLOTCFG);

  if (!rigInit) {
    rigInit = true;
    document.getElementById('fig-rigidez').on('plotly_click', data => {
      const clicked = data.points[0].y;
      selCircuit = selCircuit === clicked ? null : clicked;
      document.getElementById('circuit-sel').value = selCircuit || '';
      render();
    });
  }
}

// ── SEASON ────────────────────────────────────────────────────────────────────
function renderSeason(filt) {
  if (!filt.length) { emptyFig('fig-season'); return; }
  const sr = groupSpearman(filt, 'season').sort((a, b) => a.key.localeCompare(b.key));
  const byY = {};
  sr.forEach(d => { byY[d.key] = d.r; });

  const anns = byY['2022'] ? [{
    x: '2022', y: byY['2022'],
    text: 'Nuevo reglamento técnico', showarrow: true,
    arrowcolor: '#666', arrowhead: 2, arrowwidth: 1.5,
    font: { color: '#999', size: 11 }, ax: 52, ay: -34
  }] : [];

  Plotly.react('fig-season', [{
    x: sr.map(d => d.key), y: sr.map(d => d.r),
    mode: 'lines+markers', type: 'scatter',
    line:   { color: C.red, width: 2.5 },
    marker: { size: 10, color: '#1a1a1a', symbol: 'circle',
              line: { color: C.red, width: 2.5 } },
    hovertemplate: '<b>%{x}</b><br>Spearman r = <b>%{y:.3f}</b><extra></extra>'
  }], BL({
    showlegend: false,
    annotations: anns,
    margin: { l: 62, r: 24, t: 20, b: 52 },
    xaxis: {
      title: { text: 'Temporada', font: { size: 13, color: '#ccc' } },
      tickfont: { size: 13, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333'
    },
    yaxis: {
      title: { text: 'Spearman r', font: { size: 13, color: '#ccc' } },
      range: [0, 1.0], dtick: 0.1,
      tickfont: { size: 12, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333'
    }
  }), PLOTCFG);
}

// ── HEATMAP ───────────────────────────────────────────────────────────────────
function renderHeatmap(all) {
  const gk = {};
  all.forEach(d => {
    const k = d.circuitName + '|||' + d.season;
    (gk[k] = gk[k] || { cn: d.circuitName, s: d.season, data: [] }).data.push(d);
  });
  const pts = Object.values(gk)
    .map(g => ({ cn: g.cn, s: g.s, r: spearman(g.data) }))
    .filter(d => d.r !== null);

  const allC  = [...new Set(pts.map(d => d.cn))];
  const allS  = [...new Set(pts.map(d => d.s))].sort();
  const mR    = {};
  allC.forEach(c => {
    const rs = pts.filter(d => d.cn === c).map(d => d.r);
    mR[c] = rs.reduce((a, b) => a + b) / rs.length;
  });
  allC.sort((a, b) => mR[a] - mR[b]);  // más dinámico arriba

  const z = allC.map(c =>
    allS.map(s => {
      const pt = pts.find(d => d.cn === c && d.s === s);
      return pt ? +pt.r.toFixed(2) : null;
    })
  );

  const shapes = (selCircuit && allC.includes(selCircuit)) ? [{
    type: 'rect', xref: 'paper', yref: 'y',
    x0: 0, x1: 1,
    y0: allC.indexOf(selCircuit) - 0.5,
    y1: allC.indexOf(selCircuit) + 0.5,
    line: { color: C.red, width: 2.5 }, fillcolor: 'rgba(0,0,0,0)'
  }] : [];

  Plotly.react('fig-heatmap', [{
    z, x: allS, y: allC, type: 'heatmap',
    colorscale: [[0, C.teal], [0.35, '#2a2a2a'], [1, C.red]],
    zmin: 0, zmax: 1, hoverongaps: false,
    hovertemplate: '<b>%{y}</b>  ·  %{x}<br>Rigidez r: <b>%{z:.2f}</b><extra></extra>',
    colorbar: {
      title: { text: 'Rigidez<br>(r)', font: { size: 11, color: '#ccc' } },
      thickness: 13, len: 0.85,
      tickfont: { size: 11, color: '#bbb' }
    }
  }], BL({
    shapes,
    margin: { l: 192, r: 24, t: 18, b: 52 },
    xaxis: {
      title: { text: 'Temporada', font: { size: 13, color: '#ccc' } },
      tickfont: { size: 13, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333'
    },
    yaxis: {
      gridcolor: 'rgba(0,0,0,0)', linecolor: '#333',
      tickfont: { size: 10.5, color: '#ddd' },
      automargin: true
    }
  }), PLOTCFG);
}

// ── DOT + IQR RANGE ──────────────────────────────────────────────────────────
function quantile(sorted, q) {
  const pos  = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return base + 1 < sorted.length
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

function renderBox(all) {
  if (!all.length) { emptyFig('fig-box'); return; }
  const g = {};
  all.filter(d => d.positions_gained != null).forEach(d => {
    (g[d.circuitName] = g[d.circuitName] || []).push(d.positions_gained);
  });

  const cs = Object.keys(g);
  const st = {};
  cs.forEach(c => {
    const s = [...g[c]].sort((a, b) => a - b);
    st[c] = { q1: quantile(s, 0.25), med: quantile(s, 0.5), q3: quantile(s, 0.75), n: s.length };
  });
  cs.sort((a, b) => st[b].med - st[a].med);

  function dotColor(c) {
    if (c === selCircuit) return C.red;
    if (st[c].med >  0.5) return C.teal;
    if (st[c].med < -0.5) return '#d06060';
    return '#888';
  }

  // Barra IQR semitransparente (de Q1 a Q3)
  const iqrTrace = {
    x:           cs.map(c => st[c].q3 - st[c].q1),
    y:           cs,
    orientation: 'h', type: 'bar',
    base:        cs.map(c => st[c].q1),
    marker: {
      color: cs.map(c => c === selCircuit ? 'rgba(225,6,0,0.18)' : 'rgba(255,255,255,0.055)'),
      line:  { width: 0 }
    },
    hoverinfo: 'skip', showlegend: false, name: ''
  };

  // Punto de mediana
  const dotTrace = {
    x:    cs.map(c => st[c].med),
    y:    cs,
    mode: 'markers', type: 'scatter', name: 'Mediana',
    marker: {
      size:  cs.map(c => c === selCircuit ? 13 : 9),
      color: cs.map(c => dotColor(c)),
      line:  { color: '#111', width: 1.5 }
    },
    customdata: cs.map(c => [
      st[c].q1.toFixed(1), st[c].med.toFixed(1), st[c].q3.toFixed(1), st[c].n
    ]),
    hovertemplate:
      '<b>%{y}</b><br>' +
      'Mediana: <b>%{x:+.2f}</b> posiciones<br>' +
      'IQR: [%{customdata[0]}, %{customdata[2]}]<br>' +
      'N: %{customdata[3]}' +
      '<extra></extra>'
  };

  Plotly.react('fig-box', [iqrTrace, dotTrace], BL({
    showlegend: false, barmode: 'overlay',
    margin: { l: 192, r: 30, t: 18, b: 52 },
    xaxis: {
      title: { text: 'Posiciones ganadas (+) / perdidas (−)', font: { size: 13, color: '#ccc' } },
      tickfont: { size: 12, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333',
      zeroline: true, zerolinewidth: 2, zerolinecolor: '#3a3a3a'
    },
    yaxis: {
      gridcolor: 'rgba(0,0,0,0)', linecolor: '#333',
      tickfont: { size: 10.5, color: '#ddd' },
      automargin: true
    }
  }), PLOTCFG);
}

// ── DATOS CLIMÁTICOS ─────────────────────────────────────────────────────────
const WEATHER  = __WEATHER_JSON__;
const TOP_WET  = __TOP_WET_JSON__;

// ── WEATHER CHART — scatter con escala √ en precipitación ────────────────────
function renderWeather(wData) {
  if (!wData.length) { emptyFig('fig-weather'); return; }

  const clean = wData.filter(d => d.precipitation_mm !== null && d.avg_abs_gained !== null);

  // Transformación raíz cuadrada: separa los valores bajos (carreras secas)
  // sin distorsionar el mensaje; ticktext muestra los mm reales
  const sqrtX  = clean.map(d => Math.sqrt(d.precipitation_mm));
  const Y       = clean.map(d => d.avg_abs_gained);
  const mobMin  = Math.min(...Y);
  const mobMax  = Math.max(...Y);
  const maxSqrt = Math.sqrt(Math.max(...clean.map(d => d.precipitation_mm)));

  // ── línea de regresión sobre datos transformados ──
  function linregArr(x, y) {
    const n = x.length, mx = x.reduce((a,b)=>a+b)/n, my = y.reduce((a,b)=>a+b)/n;
    const num = x.reduce((a,xi,i) => a+(xi-mx)*(y[i]-my), 0);
    const den = x.reduce((a,xi) => a+(xi-mx)**2, 0);
    if (!den) return null;
    const m = num/den;
    return { m, b: my - m*mx };
  }
  const reg = linregArr(sqrtX, Y);

  // ticks del eje X: valores reales en mm
  const tickMM  = [0, 1, 4, 9, 16, 25].filter(v => Math.sqrt(v) <= maxSqrt + 0.5);

  // anotaciones para las 5 carreras más lluviosas visibles
  const top5 = [...clean].sort((a,b) => b.precipitation_mm - a.precipitation_mm).slice(0,5);
  const annotations = top5.map(d => ({
    x: Math.sqrt(d.precipitation_mm),
    y: d.avg_abs_gained,
    text: d.raceName.replace(' Grand Prix','').replace(' GP','') + ' ' + d.season,
    showarrow: true, arrowhead: 0, arrowwidth: 1,
    arrowcolor: '#555', ax: 36, ay: -28,
    font: { size: 9.5, color: '#aaa' }
  }));

  const traces = [
    // puntos — coloreados por movilidad
    {
      x: sqrtX, y: Y,
      mode: 'markers', type: 'scatter', name: '',
      marker: {
        size: 8, opacity: 0.78,
        color: Y,
        colorscale: [[0,'#333333'],[0.4,'#3a6ea8'],[1,'#00c9a7']],
        cmin: mobMin, cmax: mobMax,
        line: { width: 0.5, color: '#111' },
        colorbar: {
          title:    { text: 'Movilidad<br>media', font: { size: 11, color: '#ccc' } },
          thickness: 12, len: 0.65,
          tickfont: { size: 10, color: '#bbb' }, x: 1.01
        }
      },
      customdata: clean.map(d => [
        d.raceName, d.season, d.precipitation_mm.toFixed(1),
        d.avg_abs_gained.toFixed(2),
        (d.temp_max_c  ?? '—').toString(),
        (d.wind_max_kmh ?? '—').toString()
      ]),
      hovertemplate:
        '<b>%{customdata[0]}</b>  ·  %{customdata[1]}<br>' +
        '🌧 Precipitación: <b>%{customdata[2]} mm</b><br>' +
        'Movilidad media: <b>%{customdata[3]}</b> posiciones<br>' +
        '🌡 %{customdata[4]} °C  · 💨 %{customdata[5]} km/h' +
        '<extra></extra>'
    },
    // línea de regresión
    ...(reg ? [{
      x: [0, maxSqrt],
      y: [reg.b, reg.m * maxSqrt + reg.b],
      mode: 'lines', type: 'scatter', hoverinfo: 'skip',
      name: 'Tendencia',
      line: { color: 'rgba(255,255,255,0.45)', width: 2, dash: 'dash' }
    }] : [])
  ];

  Plotly.react('fig-weather', traces, BL({
    showlegend: false,
    annotations,
    margin: { l: 62, r: 24, t: 30, b: 62 },
    xaxis: {
      title:    { text: 'Precipitación el día de carrera (mm)  —  escala √',
                  font: { size: 12, color: '#ccc' } },
      tickvals: tickMM.map(v => Math.sqrt(v)),
      ticktext: tickMM.map(v => v + ' mm'),
      tickfont: { size: 11, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333',
      // línea umbral 2mm
      shapes: []
    },
    yaxis: {
      title:    { text: 'Movilidad media (|posiciones ganadas| por piloto)',
                  font: { size: 12, color: '#ccc' } },
      tickfont: { size: 12, color: '#999' },
      gridcolor: '#1f1f1f', linecolor: '#333'
    },
    shapes: [{
      type: 'line',
      x0: Math.sqrt(2), x1: Math.sqrt(2), y0: 0, y1: 1,
      xref: 'x', yref: 'paper',
      line: { color: 'rgba(255,255,255,0.18)', width: 1.5, dash: 'dot' }
    }],
    annotations: [
      ...annotations,
      { text: '← seco   |   lluvioso →',
        xref: 'x', yref: 'paper', x: Math.sqrt(2), y: 1.04,
        showarrow: false, font: { size: 9, color: '#555' } }
    ]
  }), PLOTCFG);
}

// ── BADGE CIRCUITO ACTIVO ─────────────────────────────────────────────────────
function updateBadge() {
  const bar = document.getElementById('badge-bar');
  if (selCircuit) {
    document.getElementById('badge-name').textContent = selCircuit;
    bar.style.display = 'flex';
  } else {
    bar.style.display = 'none';
  }
}

// ── ESTADO VACÍO ──────────────────────────────────────────────────────────────
function emptyFig(id) {
  Plotly.react(id, [], {
    paper_bgcolor: '#1a1a1a', plot_bgcolor: '#161616',
    annotations: [{
      text: 'Sin datos para la selección actual',
      xref: 'paper', yref: 'paper', x: 0.5, y: 0.5,
      showarrow: false,
      font: { size: 15, color: '#444', family: "'Inter',sans-serif" }
    }],
    xaxis: { visible: false }, yaxis: { visible: false },
    margin: { l: 10, r: 10, t: 10, b: 10 }
  }, { responsive: true, displaylogo: false });
}

// ── RENDER ────────────────────────────────────────────────────────────────────
function render() {
  const filt    = getFilt();
  const all     = getAllSeas();
  const weather = WEATHER.filter(d => selSeasons.has(d.season));
  updateBadge();
  renderKPIs(filt);
  renderScatter(filt);
  renderRigidez(all);
  renderSeason(filt);
  renderHeatmap(all);
  renderBox(all);
  renderWeather(weather);
}

// ── EVENTS ────────────────────────────────────────────────────────────────────
document.querySelectorAll('.sbtn').forEach(btn => {
  btn.addEventListener('click', () => {
    const s = btn.dataset.s;
    if (selSeasons.has(s)) {
      if (selSeasons.size > 1) { selSeasons.delete(s); btn.classList.remove('active'); }
    } else {
      selSeasons.add(s); btn.classList.add('active');
    }
    render();
  });
});

document.getElementById('circuit-sel').addEventListener('change', e => {
  selCircuit = e.target.value || null;
  render();
});

document.getElementById('badge-clear').addEventListener('click', () => {
  selCircuit = null;
  document.getElementById('circuit-sel').value = '';
  render();
});

document.getElementById('chk-fin').addEventListener('change', e => {
  finOnly = e.target.checked;
  render();
});

render();
"""

JS = (JS
      .replace("__DATA_JSON__",     DATA_JSON)
      .replace("__SEASONS_JSON__",  SEASONS_JSON)
      .replace("__CIRCUITS_JSON__", CIRCUITS_JSON)
      .replace("__WEATHER_JSON__",  WEATHER_JSON)
      .replace("__TOP_WET_JSON__",  TOP_WET_JSON))

# ── HTML ───────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>F1 · Parrilla vs. Resultado · 2020–2025</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
""" + CSS + """
</style>
</head>
<body>

<!-- ── HEADER STICKY ─────────────────────────────────────────────────────── -->
<div id="header">
  <div>
    <h1><span>■</span> ¿Condiciona la parrilla el resultado en F1?</h1>
    <div class="subtitle">Temporadas 2020–2025 · Jolpica F1 API</div>
  </div>
  <div class="filters">
    <div class="fg">
      <div class="flabel">Temporada</div>
      <div class="srow">
        """ + SEASON_BTNS + """
      </div>
    </div>
    <div class="fg">
      <div class="flabel">Circuito</div>
      <select id="circuit-sel">
        """ + CIRCUIT_OPTS + """
      </select>
    </div>
    <div class="fg">
      <div class="flabel">Filtro</div>
      <label class="chkrow">
        <input type="checkbox" id="chk-fin">
        Solo que terminaron
      </label>
    </div>
  </div>
</div>

<!-- ── MAIN ──────────────────────────────────────────────────────────────── -->
<div id="main">

  <!-- KPIs -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">Resumen global</div>
      <h2 class="sec-title">Panorama de la temporada 2020–2025</h2>
      <p class="sec-desc">
        Indicadores clave sobre la relación entre la posición de salida y el resultado final.
        Usa los filtros para explorar temporadas y circuitos concretos.
      </p>
    </div>
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Correlación parrilla → resultado</div>
        <div class="kpi-val red" id="kpi-r">—</div>
        <div style="font-size:.68rem;color:#555;margin-top:4px">Spearman r global</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Pilotos que ganan posiciones</div>
        <div class="kpi-val teal" id="kpi-pct">—</div>
        <div style="font-size:.68rem;color:#555;margin-top:4px">Del total de participaciones</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Circuito más rígido</div>
        <div class="kpi-val" id="kpi-rigid" style="font-size:1.05rem">—</div>
        <div style="font-size:.68rem;color:#555;margin-top:4px">Mayor correlación parrilla–resultado</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Circuito más dinámico</div>
        <div class="kpi-val" id="kpi-dynamic" style="font-size:1.05rem">—</div>
        <div style="font-size:.68rem;color:#555;margin-top:4px">Menor correlación parrilla–resultado</div>
      </div>
    </div>

    <!-- Badge circuito activo -->
    <div id="badge-bar">
      <span>Filtrando por circuito: <strong id="badge-name"></strong></span>
      <button class="badge-x" id="badge-clear" title="Quitar filtro">✕</button>
    </div>

  </div>

  <hr class="divider">

  <!-- SCATTER -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">01 — Relación global</div>
      <h2 class="sec-title">¿La posición de parrilla condiciona el resultado final?</h2>
      <p class="sec-desc">
        La línea roja muestra la <strong>posición final media</strong> de los pilotos que salieron
        desde cada posición de parrilla (1 = pole, 20 = último). La banda sombreada es ±1 desviación
        estándar. Si la línea siguiera la diagonal punteada, la parrilla determinaría el resultado
        de forma perfecta. El <strong>tooltip</strong> de cada punto responde directamente:
        "Saliendo desde P<em>X</em>, los pilotos acaban de media en P<em>Y</em>,
        y el <em>Z</em>% termina mejor de lo que salió."
        <strong>Selecciona un circuito</strong> (sección 02 o el filtro de arriba)
        para ver las carreras individuales con detalle de piloto y escudería.
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-scatter" style="height:500px"></div>
    </div>
  </div>

  <hr class="divider">

  <!-- RIGIDEZ -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">02 — Por circuito</div>
      <h2 class="sec-title">¿Qué circuitos son más rígidos competitivamente?</h2>
      <p class="sec-desc">
        La correlación de Spearman mide cuánto se parece el orden de llegada al de salida.
        Un valor cercano a <strong style="color:#e10600">1</strong> significa que salir delante casi garantiza acabar delante.
        Un valor bajo indica que la carrera genera muchos cambios de posición.
        <strong>Haz clic en una barra</strong> para filtrar todos los gráficos a ese circuito.
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-rigidez" style="height:740px"></div>
    </div>
  </div>

  <hr class="divider">

  <!-- SEASON -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">03 — Evolución temporal</div>
      <h2 class="sec-title">¿Ha cambiado la importancia de la parrilla entre 2020 y 2025?</h2>
      <p class="sec-desc">
        Evolución año a año del índice de rigidez. Un Spearman r más alto indica que ese año
        la posición de salida fue más determinante para el resultado final.
        El cambio de reglamento técnico de 2022 se señala como referencia.
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-season" style="height:340px"></div>
    </div>
  </div>

  <hr class="divider">

  <!-- HEATMAP -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">04 — Circuito × Temporada</div>
      <h2 class="sec-title">Visión completa: rigidez por circuito y por año</h2>
      <p class="sec-desc">
        Cada celda muestra el índice de rigidez (Spearman r) de un circuito en una temporada concreta.
        <span style="color:#e10600">Rojo</span> = circuito muy rígido ese año (la parrilla decide).
        <span style="color:#00c9a7">Verde</span> = alta movilidad de posiciones durante la carrera.
        Las celdas vacías indican que ese circuito no se corrió esa temporada.
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-heatmap" style="height:700px"></div>
    </div>
  </div>

  <hr class="divider">

  <!-- BOX -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">05 — Distribución</div>
      <h2 class="sec-title">¿Cuántas posiciones se ganan o pierden en cada circuito?</h2>
      <p class="sec-desc">
        Cada punto es la <strong>mediana</strong> de posiciones ganadas o perdidas en ese circuito.
        La barra semitransparente muestra el rango intercuartil (IQR: del percentil 25 al 75).
        <span style="color:#00c9a7">Verde</span> = circuitos donde los pilotos suelen ganar posiciones;
        <span style="color:#d06060">rojo</span> = donde suelen perderlas.
        La línea vertical gruesa marca el cero (sin cambio de posición).
        Ordenado de mayor a menor mediana.
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-box" style="height:680px"></div>
    </div>
  </div>

  <hr class="divider">

  <!-- CLIMA -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">06 — Clima y competitividad</div>
      <h2 class="sec-title">¿Influye la lluvia en la movilidad de posiciones?</h2>
      <p class="sec-desc">
        Cruce con datos de la API <strong>Open-Meteo</strong>: precipitación, temperatura máxima
        y viento en la ubicación del circuito el día de carrera (""" + N_WET_RACES + """ carreras
        registraron ≥ 2 mm de lluvia sobre """ + str(131) + """ analizadas).
        La movilidad se mide como la media de |posiciones ganadas| por piloto.
        Las carreras con lluvia intensa (≥ 5 mm) muestran una movilidad
        <strong style="color:#00c9a7">""" + WET_LIFT_PCT + """% superior</strong> a las carreras en seco.
        <em style="color:#555">Limitación: la precipitación diaria total puede no coincidir
        exactamente con lo ocurrido durante las horas de carrera.</em>
      </p>
    </div>
    <div class="chart-card">
      <div id="fig-weather" style="height:380px"></div>
      <div class="card-note">
        Cada punto es una carrera. El eje X usa escala raíz cuadrada para separar las carreras con poca
        lluvia (que de otro modo se apilarían todas en el cero). El color indica la movilidad:
        gris = pocas posiciones cambian, verde = muchas. La línea discontinua es la tendencia global;
        las 5 carreras más lluviosas están etiquetadas.
      </div>
    </div>
  </div>

  <hr class="divider">

  <!-- CONCLUSIONES -->
  <div class="section">
    <div class="sec-hdr">
      <div class="sec-num">Conclusiones</div>
      <h2 class="sec-title">¿Qué nos dicen los datos?</h2>
      <p class="sec-desc">
        Respuesta a las hipótesis de la Parte I a partir de
        """ + N_RACES + """ carreras disputadas entre 2020 y 2025.
      </p>
    </div>

    <!-- Métricas clave -->
    <div class="concl-grid">
      <div class="concl-card">
        <div class="concl-val" style="color:#e10600">""" + GLOBAL_R + """</div>
        <div class="concl-lbl">Correlación global (Spearman r)</div>
        <div class="concl-sub">Parrilla de salida → posición final · todas las carreras</div>
      </div>
      <div class="concl-card">
        <div class="concl-val" style="color:#00c9a7">""" + PCT_IMPROVED + """%</div>
        <div class="concl-lbl">Participaciones donde el piloto mejora su posición</div>
        <div class="concl-sub">Del total de entradas en carrera analizadas</div>
      </div>
      <div class="concl-card">
        <div class="concl-val" style="font-size:1.05rem">""" + MOST_RIGID + """</div>
        <div class="concl-lbl">Circuito más rígido</div>
        <div class="concl-sub">r = """ + MOST_RIGID_R + """ — la parrilla casi decide el resultado</div>
      </div>
      <div class="concl-card">
        <div class="concl-val" style="font-size:1.05rem">""" + MOST_DYNAMIC + """</div>
        <div class="concl-lbl">Circuito más dinámico</div>
        <div class="concl-sub">r = """ + MOST_DYNAMIC_R + """ — alta movilidad de posiciones</div>
      </div>
    </div>

    <!-- Hipótesis -->
    <div class="hyp-list">
      <div class="hyp-row">
        <span class="hyp-tag yes">H1 — Confirmada</span>
        <p class="hyp-p">
          La posición de salida condiciona de forma significativa el resultado final
          (r global = """ + GLOBAL_R + """). La correlación es alta y consistente en todas las temporadas,
          lo que indica que salir delante tiene una ventaja real y sostenida.
        </p>
      </div>
      <div class="hyp-row">
        <span class="hyp-tag yes">H2 — Confirmada</span>
        <p class="hyp-p">
          La fuerza de la correlación varía notablemente entre circuitos
          (de r = """ + MOST_DYNAMIC_R + """ en """ + MOST_DYNAMIC + """
          hasta r = """ + MOST_RIGID_R + """ en """ + MOST_RIGID + """).
          Las características del trazado influyen de forma determinante en la movilidad de posiciones.
        </p>
      </div>
      <div class="hyp-row">
        <span class="hyp-tag part">H3 — Parcialmente confirmada</span>
        <p class="hyp-p">
          Se observan diferencias entre temporadas: """ + RIGID_SEASON + """ fue el año con mayor rigidez
          (r = """ + RIGID_SEASON_R + """) y """ + OPEN_SEASON + """ el más abierto (r = """ + OPEN_SEASON_R + """).
          Sin embargo, la variación entre años es moderada en comparación con la variación entre circuitos.
        </p>
      </div>
      <div class="hyp-row">
        <span class="hyp-tag yes">H4 — Confirmada</span>
        <p class="hyp-p">
          Existen diferencias claras en la movilidad media entre circuitos.
          """ + MOST_RIGID + """ y trazados urbanos similares presentan distribuciones de posiciones ganadas
          muy concentradas alrededor de cero, mientras que circuitos como """ + MOST_DYNAMIC + """
          muestran una dispersión significativamente mayor.
        </p>
      </div>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    Fuente: Jolpica F1 API · Temporadas 2020–2025 ·
    Práctica Final de Visualización de Datos (UOC) · Marc Masramon Martí
  </div>

</div><!-- /main -->

<script>
""" + JS + """
</script>
</body>
</html>"""

# ── Escribir ────────────────────────────────────────────────────────────────────
for fname in ("index.html", "dashboard.html"):
    out = os.path.join(BASE, fname)
    with open(out, "w", encoding="utf-8") as f:
        f.write(HTML)

size_kb = os.path.getsize(os.path.join(BASE, "index.html")) / 1024
print(f"index.html + dashboard.html  ({size_kb:.0f} KB)  →  {BASE}")
print("Abre index.html en el navegador, o despliega en GitHub Pages.")
