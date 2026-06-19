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
  'Mongabay India':        { region:'National',        lang:'English', desc:"Dedicated environmental journalism covering Indian wildlife, forests & conservation policy." },
  'The Wire':              { region:'National',        lang:'English', desc:"Independent news covering environment, science & forest rights across India." },
  'The Wire Science':      { region:'National',        lang:'English', desc:"Science desk of The Wire covering ecology, conservation biology & environmental research." },
  'The Hindu':             { region:'National',        lang:'English', desc:"India's leading broadsheet with strong coverage of environment, forests & wildlife policy." },
  'Indian Express':        { region:'National',        lang:'English', desc:"National daily with dedicated environment desk covering wildlife crime, conservation & forest policy." },
  'The Indian Express':    { region:'National',        lang:'English', desc:"National daily with dedicated environment desk covering wildlife crime, conservation & forest policy." },
  'Hindustan Times':       { region:'National',        lang:'English', desc:"National daily covering wildlife conflict, poaching & conservation stories across India." },
  'Times of India':        { region:'National',        lang:'English', desc:"India's highest-circulation English daily with environment & wildlife coverage." },
  'The Times of India':    { region:'National',        lang:'English', desc:"India's highest-circulation English daily with environment & wildlife coverage." },
  'NDTV':                  { region:'National',        lang:'English', desc:"TV & digital news network with environment correspondent covering national wildlife stories." },
  'Nature India':          { region:'National',        lang:'English', desc:"Nature journal's India desk covering scientific research on biodiversity & ecology." },
  'Down To Earth':         { region:'National',        lang:'English', desc:"CSE's flagship magazine — India's most authoritative voice on environment, forests & climate policy." },
  'Scroll.in':             { region:'National',        lang:'English', desc:"Independent digital outlet with strong environment & forest rights coverage." },
  'ThePrint':              { region:'National',        lang:'English', desc:"Digital news platform with environment & policy reporting across India." },
  'Frontline Magazine':    { region:'National',        lang:'English', desc:"The Hindu's fortnightly magazine with in-depth environment, forest & tribal rights stories." },
  'India Today':           { region:'National',        lang:'English', desc:"National magazine & digital outlet with wildlife & environment coverage." },
  'Outlook India':         { region:'National',        lang:'English', desc:"National magazine covering environment, wildlife conservation & forest policy." },
  'Land Conflict Watch':   { region:'National',        lang:'English', desc:"Data journalism outlet tracking land conflicts involving forests, wildlife & tribal communities." },
  'India Development Review':{ region:'National',     lang:'English', desc:"Development-focused platform covering conservation funding, forest rights & policy." },
  'Business Standard':     { region:'National',        lang:'English', desc:"Financial daily with environment & natural resource policy reporting." },
  'ANI News':              { region:'National',        lang:'English', desc:"Wire service distributing wildlife & forest news from government and official sources across India." },
  'Research Matters':      { region:'National',        lang:'English', desc:"Science communication outlet covering ecology, biodiversity & wildlife research from Indian institutions." },
  'EastMojo':              { region:'Northeast India', lang:'English', desc:"Digital newsroom covering all 8 Northeast states — strong on wildlife, forests & environment." },
  'Northeast Now':         { region:'Northeast India', lang:'English', desc:"Northeast-focused news with environment & wildlife coverage across Assam & neighbouring states." },
  'Northeast Today':       { region:'Northeast India', lang:'English', desc:"Northeast India outlet covering Assam, Meghalaya & Arunachal wildlife & forests." },
  'Morung Express':        { region:'Nagaland',        lang:'English', desc:"Nagaland's principal English daily covering Nagaland wildlife & Amur falcon migration." },
  'Assam Tribune':         { region:'Assam',           lang:'English', desc:"Assam's oldest English daily. Covers Kaziranga, Manas, Brahmaputra ecosystem & rhino protection." },
  'The Assam Tribune':     { region:'Assam',           lang:'English', desc:"Assam's oldest English daily. Covers Kaziranga, Manas, Brahmaputra ecosystem & rhino protection." },
  'Greater Kashmir':       { region:'Jammu & Kashmir', lang:'English', desc:"J&K's largest English daily covering Dachigam, Hangul deer, snow leopard & forest management." },
  'Rising Kashmir':        { region:'Jammu & Kashmir', lang:'English', desc:"J&K-based daily with coverage of Dachigam National Park & Himalayan wildlife." },
  'Hill Post':             { region:'Himachal Pradesh',lang:'English', desc:"HP-focused outlet covering snow leopard, Himalayan brown bear & high-altitude wildlife." },
  'The Pioneer':           { region:'Central India',   lang:'English', desc:"Lucknow-based daily covering Dudhwa, Pilibhit tiger reserves & UP forest department." },
  'Telegraph India':       { region:'East India',      lang:'English', desc:"Kolkata-based daily with strong coverage of Sundarbans, Bengal tigers & Northeast wildlife." },
  'Deccan Herald':         { region:'Karnataka',       lang:'English', desc:"Bengaluru-based daily covering Nagarahole, Bandipur, Coorg forests & Western Ghats wildlife." },
  'Star of Mysore':        { region:'Karnataka',       lang:'English', desc:"Mysuru-based daily covering Nagarahole, Bandipur & Kabini wildlife." },
  'Deccan Chronicle':      { region:'South India',     lang:'English', desc:"Hyderabad-based daily covering Telangana, AP wildlife & Eastern Ghats forests." },
  'The New Indian Express':{ region:'South India',     lang:'English', desc:"South-India-focused daily with strong coverage of Western Ghats, Tamil Nadu & Kerala wildlife." },
  'The News Minute':       { region:'South India',     lang:'English', desc:"Digital outlet covering South Indian states — Nilgiris, Kerala forests & Western Ghats." },
  'The Federal':           { region:'South India',     lang:'English', desc:"Independent digital outlet covering South Indian environment & forest stories." },
  'Sambad English':        { region:'Odisha',          lang:'English', desc:"Odisha's leading daily covering Simlipal, Bhitarkanika & Chilika wildlife." },
  'OdishaBytes':           { region:'Odisha',          lang:'English', desc:"Odisha digital outlet covering state wildlife — elephants, leopards & Mahanadi basin." },
  'Gomantak Times':        { region:'Goa',             lang:'English', desc:"Goa-based daily covering Bhagwan Mahavir Wildlife Sanctuary & coastal ecology." },
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
L.control.zoom({ position: 'bottomright' }).addTo(map);
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

// ── Source info modal (mobile) ────────────────────────────────────────────────
function showSourceInfo(src) {
  const meta = SOURCE_META[src];
  if (!meta) return;
  let modal = document.getElementById('src-info-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'src-info-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.addEventListener('click', e => { if (e.target === modal) modal.setAttribute('hidden', ''); });
    modal.innerHTML = `<div id="src-info-box">
      <div id="src-info-head">
        <span id="src-info-name"></span>
        <button id="src-info-close" aria-label="Close">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <p id="src-info-desc"></p>
      <div id="src-info-tags"></div>
    </div>`;
    document.body.appendChild(modal);
    document.getElementById('src-info-close').addEventListener('click', () => modal.setAttribute('hidden', ''));
  }
  document.getElementById('src-info-name').textContent = src;
  document.getElementById('src-info-desc').textContent = meta.desc;
  document.getElementById('src-info-tags').innerHTML =
    `<span class="src-info-tag">${escapeHtml(meta.region)}</span><span class="src-info-tag">${escapeHtml(meta.lang)}</span>`;
  modal.removeAttribute('hidden');
}

// ── Source dropdown (inside filter sheet) ─────────────────────────────────────
let _srcPanelOpen = false;

function buildSourceFilters(articles) {
  _srcDropdownSources = [...new Set(articles.map(a => a.source))].sort();
  _srcDropdownSources.forEach(s => activeSrcs.add(s));

  const panel = document.getElementById('src-dropdown-panel-sheet');
  const btn   = document.getElementById('src-dropdown-btn-sheet');

  // Source search
  const searchWrap = document.createElement('div');
  searchWrap.className = 'src-search-wrap';
  searchWrap.innerHTML = `<input id="src-search-input-sheet" type="search" placeholder="Search sources…" autocomplete="off" aria-label="Search sources" />`;
  panel.appendChild(searchWrap);

  const header = document.createElement('div');
  header.className = 'src-dd-header';
  header.innerHTML = `<button class="src-dd-action" id="src-select-all">All</button><span class="src-dd-sep">·</span><button class="src-dd-action" id="src-clear-all">None</button>`;
  panel.appendChild(header);

  _srcDropdownSources.forEach(src => {
    const row = document.createElement('div');
    row.className = 'src-dd-row active';
    row.setAttribute('role','option'); row.setAttribute('aria-selected','true'); row.setAttribute('tabindex','0');
    row.dataset.src = src;
    const count   = (window._allArticles||[]).filter(a => a.source===src).length;
    const hasMeta = !!SOURCE_META[src];
    row.innerHTML = `
      <span class="src-dd-check"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg></span>
      <span class="src-dd-name">${escapeHtml(src)}</span>
      <span class="src-dd-count">${count}</span>
      ${hasMeta ? `<button class="src-info-btn src-dd-info" aria-label="About ${escapeHtml(src)}" tabindex="-1">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12.01" y2="8"/><line x1="12" y1="12" x2="12" y2="16"/></svg>
      </button>` : ''}`;

    row.addEventListener('click', () => {
      const on = _pendingSrcs.has(src);
      if (on) { _pendingSrcs.delete(src); row.classList.remove('active'); row.setAttribute('aria-selected','false'); }
      else    { _pendingSrcs.add(src);    row.classList.add('active');    row.setAttribute('aria-selected','true'); }
      updateSrcBtn();
    });
    row.addEventListener('keydown', e => { if (e.key===' '||e.key==='Enter') { e.preventDefault(); row.click(); } });

    if (hasMeta) {
      const infoBtn = row.querySelector('.src-dd-info');
      infoBtn.setAttribute('tabindex', '0');
      infoBtn.addEventListener('click', e => { e.stopPropagation(); showSourceInfo(src); });
      infoBtn.addEventListener('keydown', e => { if (e.key==='Enter'||e.key===' ') { e.preventDefault(); e.stopPropagation(); showSourceInfo(src); } });
    }

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
