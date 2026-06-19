/* WildLens Mobile App — Regional Edition map.js */

// ── Language → source mapping ─────────────────────────────────────────────────
const SOURCE_META = {
  'Mathrubhumi':          { lang:'Malayalam', region:'Kerala',        color:'#38bdf8', dot:'#0ea5e9', bg:'rgba(56,189,248,0.15)'   },
  'Malayala Manorama':    { lang:'Malayalam', region:'Kerala',        color:'#38bdf8', dot:'#0ea5e9', bg:'rgba(56,189,248,0.15)'   },
  'Manorama Online':      { lang:'Malayalam', region:'Kerala',        color:'#38bdf8', dot:'#0ea5e9', bg:'rgba(56,189,248,0.15)'   },
  'Dainik Jagran':        { lang:'Hindi',     region:'North India',   color:'#fdba74', dot:'#f97316', bg:'rgba(251,146,60,0.15)'   },
  'Amar Ujala':           { lang:'Hindi',     region:'North India',   color:'#fdba74', dot:'#f97316', bg:'rgba(251,146,60,0.15)'   },
  'Dainik Bhaskar':       { lang:'Hindi',     region:'North India',   color:'#fdba74', dot:'#f97316', bg:'rgba(251,146,60,0.15)'   },
  'Anandabazar Patrika':  { lang:'Bengali',   region:'West Bengal',   color:'#6ee7b7', dot:'#34d399', bg:'rgba(52,211,153,0.15)'   },
  'Pratidin':             { lang:'Bengali',   region:'West Bengal',   color:'#6ee7b7', dot:'#34d399', bg:'rgba(52,211,153,0.15)'   },
  'Sangbad Pratidin':     { lang:'Bengali',   region:'West Bengal',   color:'#6ee7b7', dot:'#34d399', bg:'rgba(52,211,153,0.15)'   },
  'Dinakaran':            { lang:'Tamil',     region:'Tamil Nadu',    color:'#fde68a', dot:'#fbbf24', bg:'rgba(251,191,36,0.15)'   },
  'Dinamalar':            { lang:'Tamil',     region:'Tamil Nadu',    color:'#fde68a', dot:'#fbbf24', bg:'rgba(251,191,36,0.15)'   },
  'Sakshi':               { lang:'Telugu',    region:'Andhra/Telangana', color:'#ddd6fe', dot:'#a78bfa', bg:'rgba(167,139,250,0.15)' },
  'Eenadu':               { lang:'Telugu',    region:'Andhra/Telangana', color:'#ddd6fe', dot:'#a78bfa', bg:'rgba(167,139,250,0.15)' },
  'Prajavani':            { lang:'Kannada',   region:'Karnataka',     color:'#fbcfe8', dot:'#f472b6', bg:'rgba(244,114,182,0.15)'  },
  'Vijaya Karnataka':     { lang:'Kannada',   region:'Karnataka',     color:'#fbcfe8', dot:'#f472b6', bg:'rgba(244,114,182,0.15)'  },
  'Loksatta':             { lang:'Marathi',   region:'Maharashtra',   color:'#d9f99d', dot:'#a3e635', bg:'rgba(163,230,53,0.15)'   },
  'Sakal':                { lang:'Marathi',   region:'Maharashtra',   color:'#d9f99d', dot:'#a3e635', bg:'rgba(163,230,53,0.15)'   },
  'Lokmat':               { lang:'Marathi',   region:'Maharashtra',   color:'#d9f99d', dot:'#a3e635', bg:'rgba(163,230,53,0.15)'   },
  'Purvanchal Prahari':   { lang:'Other',     region:'Northeast',     color:'#cbd5e1', dot:'#94a3b8', bg:'rgba(148,163,184,0.15)'  },
  'Sentinel Assam':       { lang:'Other',     region:'Assam',         color:'#cbd5e1', dot:'#94a3b8', bg:'rgba(148,163,184,0.15)'  },
  'Prameya News':         { lang:'Other',     region:'Odisha',        color:'#cbd5e1', dot:'#94a3b8', bg:'rgba(148,163,184,0.15)'  },
};

const LANG_COLORS = {
  Hindi:     { color:'#fdba74', dot:'#f97316', bg:'rgba(251,146,60,0.15)'   },
  Bengali:   { color:'#6ee7b7', dot:'#34d399', bg:'rgba(52,211,153,0.15)'   },
  Tamil:     { color:'#fde68a', dot:'#fbbf24', bg:'rgba(251,191,36,0.15)'   },
  Telugu:    { color:'#ddd6fe', dot:'#a78bfa', bg:'rgba(167,139,250,0.15)'  },
  Kannada:   { color:'#fbcfe8', dot:'#f472b6', bg:'rgba(244,114,182,0.15)'  },
  Malayalam: { color:'#bae6fd', dot:'#38bdf8', bg:'rgba(56,189,248,0.15)'   },
  Marathi:   { color:'#d9f99d', dot:'#a3e635', bg:'rgba(163,230,53,0.15)'   },
  Other:     { color:'#cbd5e1', dot:'#94a3b8', bg:'rgba(148,163,184,0.15)'  },
};

function getSourceLang(source) {
  return (SOURCE_META[source] || {}).lang || 'Other';
}
function getLangStyle(lang) {
  return LANG_COLORS[lang] || LANG_COLORS.Other;
}

// ── Map ───────────────────────────────────────────────────────────────────────
const map = L.map('map', {
  center: [22, 82], zoom: 5,
  minZoom: 4, maxZoom: 16,
  zoomSnap: 0.25,
  maxBounds: [[1,63],[41,102]],
  maxBoundsViscosity: 1.0,
  zoomControl: false,
  tap: true,
  preferCanvas: true,
});
L.control.zoom({ position: 'bottomright' }).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://carto.com/" target="_blank" rel="noopener">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
  subdomains: 'abcd', maxZoom: 19,
}).addTo(map);
map.fitBounds([[3.5,66],[38.5,99]], { padding:[10,10] });

fetch('../../india_boundary.geojson')
  .then(r => r.json())
  .then(data => L.geoJSON(data, { style:{ color:'#fff', weight:1, opacity:0.25, fill:false }, interactive:false }).addTo(map))
  .catch(() => {});

// ── Clusters ──────────────────────────────────────────────────────────────────
const clusters = L.markerClusterGroup({
  maxClusterRadius: 50,
  spiderfyOnMaxZoom: true,
  showCoverageOnHover: false,
  iconCreateFunction(cluster) {
    const count = cluster.getChildCount();
    const large = count >= 10 ? ' large' : '';
    return L.divIcon({ html:`<div class="cluster-icon${large}">${count}</div>`, className:'', iconSize: large ? [46,46]:[38,38] });
  },
});
map.addLayer(clusters);

// ── State ─────────────────────────────────────────────────────────────────────
let allArticles = [], allMarkers = [];
const activeLangs = new Set(['Hindi','Bengali','Tamil','Telugu','Kannada','Malayalam','Marathi','Other']);
const activeSrcs  = new Set();
let _srcDropdownSources = [];
let _pendingSrcs = new Set();

// ── Helpers ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function markerRadius(published) {
  const days = (Date.now() - new Date(published).getTime()) / 86400000;
  return Math.max(5, 10 - days * 0.12);
}
function formatDate(d) {
  if (!d) return '';
  try { return new Date(d).toLocaleDateString('en-IN',{ day:'numeric', month:'short', year:'numeric' }); }
  catch { return d; }
}
function updateCountBadge(shown, total) {
  const el = document.getElementById('count-badge');
  const barH = document.getElementById('bottom-bar').offsetHeight;
  el.style.bottom = (barH + 10) + 'px';
  el.innerHTML = shown === total
    ? `<b>${total}</b> regional articles`
    : `<b>${shown}</b> of ${total} articles`;
  document.getElementById('article-count').innerHTML =
    shown === total ? `<b>${total}</b> articles` : `<b>${shown}</b> / ${total}`;
}

// ── Render ────────────────────────────────────────────────────────────────────
function applyFilters() {
  const query    = (document.getElementById('search-input').value||'').toLowerCase().trim();
  const dateFrom = document.getElementById('date-from-sheet').value;
  const dateTo   = document.getElementById('date-to-sheet').value;

  const filtered = allMarkers.filter(({ article:a }) => {
    const lang = getSourceLang(a.source);
    if (!activeLangs.has(lang))              return false;
    if (!activeSrcs.has(a.source))           return false;
    if (dateFrom && a.published < dateFrom)  return false;
    if (dateTo   && a.published > dateTo)    return false;
    if (query && !((a.headline||'').toLowerCase().includes(query) ||
                   (a.place_name||'').toLowerCase().includes(query) ||
                   (a.source||'').toLowerCase().includes(query)))  return false;
    return true;
  });

  clusters.clearLayers();
  filtered.forEach(({ marker }) => clusters.addLayer(marker));
  updateCountBadge(filtered.length, allArticles.length);
}

// ── Article card ──────────────────────────────────────────────────────────────
function showArticleCard(article) {
  const lang  = getSourceLang(article.source);
  const style = getLangStyle(lang);
  const card  = document.getElementById('article-card');

  const badge = document.getElementById('card-lang-badge');
  badge.style.background = style.bg;
  badge.style.color      = style.color;
  document.getElementById('card-lang-dot').style.background = style.dot;
  document.getElementById('card-lang-label').textContent    = lang;
  document.getElementById('card-source-badge').textContent  = article.source;
  document.getElementById('card-headline').textContent      = article.headline;

  // English subtitle if headline_en is available (for non-English articles)
  const enEl = document.getElementById('card-headline-en');
  if (article.headline_en && article.headline_en !== article.headline) {
    enEl.textContent    = article.headline_en;
    enEl.style.display  = '';
  } else {
    enEl.style.display  = 'none';
  }

  document.getElementById('card-place').textContent       = article.place_name || '';
  document.getElementById('card-source-date').textContent = `${article.source} · ${formatDate(article.published)}`;
  document.getElementById('card-read-btn').href           = article.url;

  card.setAttribute('aria-hidden', 'false');
  card.classList.add('visible');

  document.getElementById('filter-overlay').style.pointerEvents = 'none';
  document.getElementById('filter-overlay').style.opacity       = '0.3';
  document.getElementById('filter-overlay').addEventListener('click', hideArticleCard, { once:true });
}

function hideArticleCard() {
  const card = document.getElementById('article-card');
  card.classList.remove('visible');
  card.setAttribute('aria-hidden', 'true');
  const overlay = document.getElementById('filter-overlay');
  overlay.style.opacity       = '0';
  overlay.style.pointerEvents = 'none';
}

map.on('click', hideArticleCard);

// ── Filter sheet ──────────────────────────────────────────────────────────────
function openFilterSheet() {
  _pendingSrcs = new Set(activeSrcs);
  const sheet   = document.getElementById('filter-sheet');
  const overlay = document.getElementById('filter-overlay');
  const btn     = document.getElementById('filters-btn');
  sheet.classList.add('visible');
  sheet.setAttribute('aria-hidden', 'false');
  overlay.classList.add('visible');
  btn.setAttribute('aria-expanded', 'true');
  hideArticleCard();
}

function closeFilterSheet() {
  const sheet   = document.getElementById('filter-sheet');
  const overlay = document.getElementById('filter-overlay');
  const btn     = document.getElementById('filters-btn');
  sheet.classList.remove('visible');
  sheet.setAttribute('aria-hidden', 'true');
  overlay.classList.remove('visible');
  btn.setAttribute('aria-expanded', 'false');
}

document.getElementById('filters-btn').addEventListener('click', openFilterSheet);
document.getElementById('filter-overlay').addEventListener('click', () => {
  if (document.getElementById('filter-sheet').classList.contains('visible')) closeFilterSheet();
  else hideArticleCard();
});
document.querySelector('.sheet-close').addEventListener('click', closeFilterSheet);

let _sheetTouchY = 0;
const filterSheet = document.getElementById('filter-sheet');
filterSheet.addEventListener('touchstart', e => { _sheetTouchY = e.touches[0].clientY; }, { passive:true });
filterSheet.addEventListener('touchend',   e => {
  if (e.changedTouches[0].clientY - _sheetTouchY > 70) closeFilterSheet();
}, { passive:true });

document.getElementById('sheet-apply-btn').addEventListener('click', () => {
  activeSrcs.clear();
  _pendingSrcs.forEach(s => activeSrcs.add(s));
  closeFilterSheet();
  applyFilters();
});

document.getElementById('sheet-reset-btn').addEventListener('click', () => {
  _srcDropdownSources.forEach(s => { activeSrcs.add(s); _pendingSrcs.add(s); });
  document.querySelectorAll('#src-dropdown-panel-sheet .src-dd-row').forEach(r => {
    r.classList.add('active'); r.setAttribute('aria-selected','true');
  });
  updateSrcBtn();
  setDefaultDates(allArticles);
  Object.keys(LANG_COLORS).forEach(l => activeLangs.add(l));
  document.querySelectorAll('#cat-strip .lang-chip').forEach(ch => {
    ch.classList.remove('inactive'); ch.setAttribute('aria-pressed','true');
  });
  closeFilterSheet();
  applyFilters();
});

document.addEventListener('keydown', e => { if (e.key==='Escape') { closeFilterSheet(); hideArticleCard(); } });

// ── Language chips ────────────────────────────────────────────────────────────
document.querySelectorAll('#cat-strip .lang-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const lang = chip.dataset.lang;
    const active = activeLangs.has(lang);
    if (active && activeLangs.size === 1) return; // keep at least one
    if (active) { activeLangs.delete(lang); chip.classList.add('inactive'); chip.setAttribute('aria-pressed','false'); }
    else        { activeLangs.add(lang);    chip.classList.remove('inactive'); chip.setAttribute('aria-pressed','true'); }
    applyFilters();
  });
});

// ── Source dropdown ───────────────────────────────────────────────────────────
let _srcPanelOpen = false;

function buildSourceFilters(articles) {
  _srcDropdownSources = [...new Set(articles.map(a => a.source))].sort();
  _srcDropdownSources.forEach(s => activeSrcs.add(s));

  const panel = document.getElementById('src-dropdown-panel-sheet');
  const btn   = document.getElementById('src-dropdown-btn-sheet');

  const searchWrap = document.createElement('div');
  searchWrap.className = 'src-search-wrap';
  searchWrap.innerHTML = `<input id="src-search-input-sheet" type="search" placeholder="Search sources…" autocomplete="off" aria-label="Search sources" />`;
  panel.appendChild(searchWrap);

  const header = document.createElement('div');
  header.className = 'src-dd-header';
  header.innerHTML = `<button class="src-dd-action" id="src-select-all">All</button><span class="src-dd-sep">·</span><button class="src-dd-action" id="src-clear-all">None</button>`;
  panel.appendChild(header);

  _srcDropdownSources.forEach(src => {
    const meta  = SOURCE_META[src] || {};
    const lang  = meta.lang || 'Other';
    const row   = document.createElement('div');
    row.className = 'src-dd-row active';
    row.setAttribute('role','option'); row.setAttribute('aria-selected','true'); row.setAttribute('tabindex','0');
    row.dataset.src = src;
    const count = (window._allArticles||[]).filter(a => a.source===src).length;
    const style = getLangStyle(lang);
    row.innerHTML = `
      <span class="src-dd-check"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg></span>
      <span class="src-dd-name">${escapeHtml(src)}</span>
      <span class="src-dd-lang-dot" style="background:${style.dot};width:6px;height:6px;border-radius:50%;display:inline-block;margin-left:auto;margin-right:4px;flex-shrink:0" title="${escapeHtml(lang)}"></span>
      <span class="src-dd-count">${count}</span>`;

    row.addEventListener('click', () => {
      const on = _pendingSrcs.has(src);
      if (on) { _pendingSrcs.delete(src); row.classList.remove('active'); row.setAttribute('aria-selected','false'); }
      else    { _pendingSrcs.add(src);    row.classList.add('active');    row.setAttribute('aria-selected','true'); }
      updateSrcBtn();
    });
    row.addEventListener('keydown', e => { if (e.key===' '||e.key==='Enter') { e.preventDefault(); row.click(); } });
    panel.appendChild(row);
  });

  document.getElementById('src-select-all').addEventListener('click', e => {
    e.stopPropagation();
    _srcDropdownSources.forEach(s => _pendingSrcs.add(s));
    panel.querySelectorAll('.src-dd-row').forEach(r => { r.classList.add('active'); r.setAttribute('aria-selected','true'); });
    updateSrcBtn();
  });
  document.getElementById('src-clear-all').addEventListener('click', e => {
    e.stopPropagation();
    _pendingSrcs.clear();
    panel.querySelectorAll('.src-dd-row').forEach(r => { r.classList.remove('active'); r.setAttribute('aria-selected','false'); });
    updateSrcBtn();
  });

  document.getElementById('src-search-input-sheet').addEventListener('input', function() {
    const q = this.value.toLowerCase();
    panel.querySelectorAll('.src-dd-row').forEach(r => {
      r.style.display = r.dataset.src.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  btn.addEventListener('click', () => {
    _srcPanelOpen = !_srcPanelOpen;
    panel.hidden = !_srcPanelOpen;
    btn.setAttribute('aria-expanded', String(_srcPanelOpen));
  });

  updateSrcBtn();
}

function updateSrcBtn() {
  const total  = _srcDropdownSources.length;
  const active = _srcDropdownSources.filter(s => _pendingSrcs.has(s)).length;
  const label  = document.getElementById('src-dropdown-label-sheet');
  const btn    = document.getElementById('src-dropdown-btn-sheet');
  label.textContent = active===total ? 'All sources' : active===0 ? 'No sources' : `${active} of ${total} sources`;
  btn.classList.toggle('src-btn-filtered', active!==total);
}

// ── Date defaults ─────────────────────────────────────────────────────────────
function setDefaultDates(articles) {
  const dates = articles.map(a=>a.published).filter(Boolean).sort();
  if (dates.length) {
    document.getElementById('date-from-sheet').value = dates[0];
    document.getElementById('date-to-sheet').value   = dates[dates.length-1];
  }
}

document.getElementById('date-from-sheet').addEventListener('change', () => {
  if (!document.getElementById('filter-sheet').classList.contains('visible')) applyFilters();
});
document.getElementById('date-to-sheet').addEventListener('change', () => {
  if (!document.getElementById('filter-sheet').classList.contains('visible')) applyFilters();
});

// ── Search ────────────────────────────────────────────────────────────────────
let _searchTimer;
const searchInput = document.getElementById('search-input');
const searchClear = document.getElementById('search-clear');

searchInput.addEventListener('input', () => {
  searchClear.style.display = searchInput.value ? 'flex' : 'none';
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(applyFilters, 250);
});
searchClear.addEventListener('click', () => {
  searchInput.value = '';
  searchClear.style.display = 'none';
  searchInput.focus();
  applyFilters();
});

// ── Load data ─────────────────────────────────────────────────────────────────
fetch('../../regional/news.json')
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(articles => {
    if (!articles.length) {
      document.getElementById('article-count').textContent = 'No articles yet';
      return;
    }

    allArticles = articles;
    window._allArticles = articles;

    allMarkers = articles.map(a => {
      const lang   = getSourceLang(a.source);
      const style  = getLangStyle(lang);
      const radius = markerRadius(a.published);

      const marker = L.circleMarker([a.lat, a.lon], {
        radius, color: style.dot, fillColor: style.dot,
        fillOpacity: 0.85, weight: 1.5, opacity: 0.9,
      });

      marker.on('click', e => { L.DomEvent.stopPropagation(e); showArticleCard(a); });
      marker.on('mouseover', function() { this.setStyle({ weight:2.5, fillOpacity:1 }); });
      marker.on('mouseout',  function() { this.setStyle({ weight:1.5, fillOpacity:0.85 }); });

      return { article:a, marker };
    });

    buildSourceFilters(articles);
    setDefaultDates(articles);
    applyFilters();
  })
  .catch(err => {
    console.error('Failed to load regional news.json:', err);
    document.getElementById('article-count').textContent = 'Failed to load articles';
  });
