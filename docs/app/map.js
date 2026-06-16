/* WildLens Mobile App — map.js */

// ── Constants ─────────────────────────────────────────────────────────────────
const CATEGORY_COLORS = {
  poaching:     '#ef4444',
  discovery:    '#f59e0b',
  conflict:     '#f97316',
  research:     '#06b6d4',
  conservation: '#818cf8',
};
const CATEGORY_LABELS = {
  poaching:     'Poaching & Crime',
  discovery:    'Species Discovery',
  conflict:     'Human-Wildlife Conflict',
  research:     'Research & Science',
  conservation: 'Conservation & Policy',
};
const CATEGORY_BADGE_STYLES = {
  poaching:     { bg: 'rgba(239,68,68,0.15)',   color: '#fca5a5', dot: '#ef4444' },
  discovery:    { bg: 'rgba(245,158,11,0.15)',  color: '#fcd34d', dot: '#f59e0b' },
  conflict:     { bg: 'rgba(249,115,22,0.15)',  color: '#fdba74', dot: '#f97316' },
  research:     { bg: 'rgba(6,182,212,0.15)',   color: '#67e8f9', dot: '#06b6d4' },
  conservation: { bg: 'rgba(129,140,248,0.15)', color: '#a5b4fc', dot: '#818cf8' },
};
const CATEGORY_KEYWORDS = {
  poaching:  ['poach','snare','traffick','smuggl','ivory','wildlife crime','confiscat','illegal hunt'],
  discovery: ['new species','new-to-science','records first','first record','scientists discover'],
  conflict:  ['elephant attack','leopard attack','tiger attack','bear attack','mauled','human-wildlife','man-animal'],
  research:  ['finds study','reveals survey','population rises','population survey','census','camera trap'],
};
const SOURCE_META = {
  'Mongabay India':    { region:'National',        lang:'English', desc:'Dedicated environmental journalism covering Indian wildlife, forests & conservation.' },
  'The Wire':          { region:'National',        lang:'English', desc:'Independent news covering environment, science & forest rights across India.' },
  'The Hindu':         { region:'National',        lang:'English', desc:"India's leading broadsheet with strong coverage of wildlife & forest policy." },
  'Indian Express':    { region:'National',        lang:'English', desc:'National daily with dedicated environment desk covering wildlife & conservation.' },
  'Hindustan Times':   { region:'National',        lang:'English', desc:'National daily covering wildlife conflict, poaching & conservation stories.' },
  'Times of India':    { region:'National',        lang:'English', desc:"India's highest-circulation English daily with wildlife coverage." },
  'NDTV':              { region:'National',        lang:'English', desc:'TV & digital network with environment correspondent.' },
  'EastMojo':          { region:'Northeast India', lang:'English', desc:'Digital newsroom covering all 8 Northeast states — wildlife & forests.' },
  'Northeast Now':     { region:'Northeast India', lang:'English', desc:'Northeast-focused news with wildlife coverage across Assam & neighbours.' },
  'Assam Tribune':     { region:'Assam',           lang:'English', desc:"Assam's oldest English daily. Covers Kaziranga, rhino & Manas." },
  'Greater Kashmir':   { region:'J&K',             lang:'English', desc:"J&K's largest daily — Hangul deer, snow leopard & forest coverage." },
  'Deccan Herald':     { region:'Karnataka',       lang:'English', desc:'Bengaluru-based daily covering Nagarahole, Bandipur & Western Ghats.' },
};

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
L.control.zoom({ position: 'topright' }).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://carto.com/" target="_blank" rel="noopener">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
  subdomains: 'abcd', maxZoom: 19,
}).addTo(map);
map.fitBounds([[3.5,66],[38.5,99]], { padding:[10,10] });

fetch('../india_boundary.geojson')
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
const activeCats = new Set(['poaching','discovery','conflict','research','conservation']);
const activeSrcs = new Set();
let _srcDropdownSources = [];
let _pendingSrcs = new Set();   // holds changes until Apply is tapped
let _pendingFrom = '', _pendingTo = '';

// ── Helpers ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function categorize(headline) {
  const lower = (headline||'').toLowerCase();
  for (const [cat, words] of Object.entries(CATEGORY_KEYWORDS)) {
    if (words.some(w => lower.includes(w))) return cat;
  }
  return 'conservation';
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
    ? `<b>${total}</b> articles on map`
    : `<b>${shown}</b> of ${total} articles`;
  document.getElementById('article-count').innerHTML =
    shown === total ? `<b>${total}</b> articles` : `<b>${shown}</b> / ${total}`;
}

// ── Render ────────────────────────────────────────────────────────────────────
function applyFilters() {
  const query   = (document.getElementById('search-input').value||'').toLowerCase().trim();
  const dateFrom = document.getElementById('date-from-sheet').value;
  const dateTo   = document.getElementById('date-to-sheet').value;

  const filtered = allMarkers.filter(({ article:a }) => {
    if (!activeCats.has(categorize(a.headline))) return false;
    if (!activeSrcs.has(a.source))               return false;
    if (dateFrom && a.published < dateFrom)       return false;
    if (dateTo   && a.published > dateTo)         return false;
    if (query && !((a.headline||'').toLowerCase().includes(query) ||
                   (a.place_name||'').toLowerCase().includes(query) ||
                   (a.source||'').toLowerCase().includes(query))) return false;
    return true;
  });

  clusters.clearLayers();
  filtered.forEach(({ marker }) => clusters.addLayer(marker));
  updateCountBadge(filtered.length, allArticles.length);
}

// ── Article card ──────────────────────────────────────────────────────────────
function showArticleCard(article) {
  const cat   = categorize(article.headline);
  const style = CATEGORY_BADGE_STYLES[cat];
  const card  = document.getElementById('article-card');

  document.getElementById('card-cat-badge').style.cssText =
    `background:${style.bg};color:${style.color}`;
  document.getElementById('card-cat-dot').style.background = style.dot;
  document.getElementById('card-cat-label').textContent    = CATEGORY_LABELS[cat];
  document.getElementById('card-headline').textContent     = article.headline;
  document.getElementById('card-place').textContent        = article.place_name || '';
  document.getElementById('card-source-date').textContent  = `${article.source} · ${formatDate(article.published)}`;
  document.getElementById('card-read-btn').href            = article.url;

  card.setAttribute('aria-hidden', 'false');
  card.classList.add('visible');

  // Dim map slightly
  document.getElementById('filter-overlay').style.pointerEvents = 'none';
  document.getElementById('filter-overlay').style.opacity = '0.3';
  document.getElementById('filter-overlay').addEventListener('click', hideArticleCard, { once:true });
}

function hideArticleCard() {
  const card = document.getElementById('article-card');
  card.classList.remove('visible');
  card.setAttribute('aria-hidden', 'true');
  const overlay = document.getElementById('filter-overlay');
  overlay.style.opacity = '0';
  overlay.style.pointerEvents = 'none';
}

map.on('click', hideArticleCard);

// ── Filter sheet ──────────────────────────────────────────────────────────────
function openFilterSheet() {
  // Snapshot current state into pending
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

// Swipe-down to close sheet
let _sheetTouchY = 0;
const filterSheet = document.getElementById('filter-sheet');
filterSheet.addEventListener('touchstart', e => { _sheetTouchY = e.touches[0].clientY; }, { passive:true });
filterSheet.addEventListener('touchend', e => {
  if (e.changedTouches[0].clientY - _sheetTouchY > 70) closeFilterSheet();
}, { passive:true });

// Apply button — commit pending state
document.getElementById('sheet-apply-btn').addEventListener('click', () => {
  activeSrcs.clear();
  _pendingSrcs.forEach(s => activeSrcs.add(s));
  closeFilterSheet();
  applyFilters();
});

// Reset button
document.getElementById('sheet-reset-btn').addEventListener('click', () => {
  _srcDropdownSources.forEach(s => { activeSrcs.add(s); _pendingSrcs.add(s); });
  document.querySelectorAll('#src-dropdown-panel-sheet .src-dd-row').forEach(r => {
    r.classList.add('active'); r.setAttribute('aria-selected','true');
  });
  updateSrcBtn();
  setDefaultDates(allArticles);
  ['poaching','discovery','conflict','research','conservation'].forEach(c => activeCats.add(c));
  document.querySelectorAll('#cat-strip .cat-chip').forEach(ch => {
    ch.classList.remove('inactive'); ch.setAttribute('aria-pressed','true');
  });
  closeFilterSheet();
  applyFilters();
});

// Escape key
document.addEventListener('keydown', e => { if (e.key==='Escape') { closeFilterSheet(); hideArticleCard(); } });

// ── Category chips ────────────────────────────────────────────────────────────
document.querySelectorAll('#cat-strip .cat-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const cat = chip.dataset.cat;
    const active = activeCats.has(cat);
    if (active && activeCats.size === 1) return; // keep at least one
    if (active) { activeCats.delete(cat); chip.classList.add('inactive'); chip.setAttribute('aria-pressed','false'); }
    else        { activeCats.add(cat);    chip.classList.remove('inactive'); chip.setAttribute('aria-pressed','true'); }
    applyFilters();
  });
});

// ── Source dropdown (inside filter sheet) ─────────────────────────────────────
let _srcPanelOpen = false;

function buildSourceFilters(articles) {
  _srcDropdownSources = [...new Set(articles.map(a => a.source))].sort();
  _srcDropdownSources.forEach(s => activeSrcs.add(s));

  const panel = document.getElementById('src-dropdown-panel-sheet');
  const btn   = document.getElementById('src-dropdown-btn-sheet');

  const header = document.createElement('div');
  header.className = 'src-dd-header';
  header.innerHTML = `<button class="src-dd-action" id="src-select-all">All</button><span class="src-dd-sep">·</span><button class="src-dd-action" id="src-clear-all">None</button>`;
  panel.appendChild(header);

  _srcDropdownSources.forEach(src => {
    const row = document.createElement('div');
    row.className = 'src-dd-row active';
    row.setAttribute('role','option'); row.setAttribute('aria-selected','true'); row.setAttribute('tabindex','0');
    row.dataset.src = src;
    const count = (window._allArticles||[]).filter(a => a.source===src).length;
    row.innerHTML = `
      <span class="src-dd-check"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg></span>
      <span class="src-dd-name">${escapeHtml(src)}</span>
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
fetch('../news.json')
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(articles => {
    if (!articles.length) {
      document.getElementById('article-count').textContent = 'No articles yet';
      return;
    }

    allArticles = articles;
    window._allArticles = articles;

    allMarkers = articles.map(a => {
      const cat    = categorize(a.headline);
      const color  = CATEGORY_COLORS[cat];
      const radius = markerRadius(a.published);

      const marker = L.circleMarker([a.lat, a.lon], {
        radius, color, fillColor: color,
        fillOpacity: 0.85, weight: 1.5, opacity: 0.9,
      });

      // Mobile: tap → bottom card (no Leaflet popup)
      marker.on('click', e => {
        L.DomEvent.stopPropagation(e);
        showArticleCard(a);
      });
      marker.on('mouseover', function() { this.setStyle({ weight:2.5, fillOpacity:1 }); });
      marker.on('mouseout',  function() { this.setStyle({ weight:1.5, fillOpacity:0.85 }); });

      return { article:a, marker };
    });

    buildSourceFilters(articles);
    setDefaultDates(articles);
    applyFilters();
  })
  .catch(err => {
    console.error('Failed to load news.json:', err);
    document.getElementById('article-count').textContent = 'Failed to load articles';
  });
