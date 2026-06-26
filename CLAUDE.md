# WildLens — Master Project Memory

---

## ⚠️ TWO SYSTEMS — READ THIS FIRST

V1 is LIVE at wildlens.in. It is complete, in production, and actively maintained.
V2 is the ecological intelligence system. It is in build under v2/ directory.
They share spatial reference datasets only. Never mix code between them.

---

# V1 — Wildlife News Map (LIVE — actively maintained)

## Project goal
A free, zero-ongoing-cost web platform that displays Indian wildlife
and environment news as pins on an interactive map of India.
Runs entirely on GitHub Actions (processing) + GitHub Pages (hosting).
No backend server. No paid APIs.

## Architecture
GitHub Actions runs fetch_and_process.py every 6 hours:
  1. Pulls articles from RSS feeds (filtered by wildlife keywords)
  2. Extracts the most specific Indian location from each article
  3. Geocodes that location to lat/lon
  4. Writes results to docs/news.json
GitHub Pages serves docs/ as a static site.
Leaflet.js map reads docs/news.json and renders pins.
User clicks pin → popup with headline + source → click → original article.

## Folder structure
.github/workflows/fetch_news.yml
scripts/fetch_and_process.py
scripts/extractor.py
scripts/geocoder.py
scripts/requirements.txt
data/india_pa_gazetteer.csv
docs/index.html
docs/map.js
docs/style.css

## Stack
- Python 3.11
- feedparser (RSS fetching)
- spaCy with en_core_web_trf model (NER location extraction)
- geopy Nominatim (geocoding, free)
- Leaflet.js 1.9.x via CDN (map rendering)
- GitHub Actions (scheduled pipeline)
- GitHub Pages serving from /docs folder

## File responsibilities

### scripts/fetch_and_process.py
Main pipeline script. Called by GitHub Actions.
Steps:
  1. Load existing docs/news.json (if exists) to check already-processed URLs
  2. Fetch articles from all sources in scripts/sources.yaml
  3. Filter by keywords
  4. For each NEW article only (URL not in existing news.json):
     a. Run extractor.py to get place name
     b. Run geocoder.py to get lat/lon
     c. Skip article if geocoding returns None
  5. Merge new results with existing news.json
  6. Write final array to docs/news.json

### scripts/extractor.py
Two-pass location extraction. No API calls whatsoever.
Pass 1: Load data/india_pa_gazetteer.csv. Search article
  title + first 600 chars of description for any PA name match.
  If match found, return (place_name, lat, lon) directly.
  Skip geocoding entirely for these — gazetteer has coordinates.
Pass 2: If no gazetteer match, use spaCy en_core_web_trf to
  extract all GPE and LOC entities from article text.
  Return the most specific one (prefer longer, more specific names).
  Return None if nothing found.

### scripts/geocoder.py
Takes a place name string.
Uses geopy Nominatim with user_agent="wildlife-news-map-india".
Adds ", India" to every query to bias results.
Enforces 1 second delay between requests (Nominatim ToS).
Returns (lat, lon) tuple or None if not found.
Never geocode the same place name twice — use a simple
in-memory dict cache within each run.

### data/india_pa_gazetteer.csv
CSV with columns: name, lat, lon, type
Covers: tiger reserves, national parks, wildlife sanctuaries,
  biosphere reserves, elephant reserves, major forest divisions.
Populate with at least 200 entries covering all Indian states.
Include common alternate names and abbreviations as separate rows.
Example rows:
  Nagarahole National Park,12.0833,76.1667,national_park
  Rajiv Gandhi National Park,12.0833,76.1667,national_park
  Kabini,12.0833,76.1667,forest_range

### docs/news.json
Auto-generated. Do not edit manually.
Format:
[
  {
    "headline": "...",
    "url": "...",
    "source": "...",
    "published": "YYYY-MM-DD",
    "place_name": "...",
    "lat": 00.0000,
    "lon": 00.0000
  }
]

### docs/index.html
Single page. Loads Leaflet.js from CDN.
Full screen map of India (default bounds lat 6-37, lon 68-98, zoom 5).
Dark or nature-themed tile layer.
Loads docs/news.json via fetch().
Renders circle markers sized by recency (newer = slightly larger).
Click marker → popup with headline, source name, date,
  and "Read article" link opening in new tab.
Clean minimal UI. No frameworks. No build step.

### docs/map.js
Fetches news.json.
Groups pins within 40km into clusters using Leaflet.markercluster CDN plugin.
Color code markers by category if detectable
  (poaching=red, sighting=green, conservation=blue, other=grey).
Shows total article count in top-right corner.

### docs/style.css
Minimal. Map takes full viewport.
Popup styled cleanly. Mobile responsive.

### .github/workflows/fetch_news.yml
Trigger: schedule cron every 6 hours + manual workflow_dispatch.
Steps:
  - actions/checkout@v4
  - Set up Python 3.11
  - pip install -r scripts/requirements.txt
  - python -m spacy download en_core_web_trf
  - python scripts/fetch_and_process.py
  - Git commit and push docs/news.json if changed
    (use: git config user.email "action@github.com")
    (only commit if news.json actually changed)

## RSS sources
- https://www.downtoearth.org/rss/wildlife
- https://www.downtoearth.org/rss/forests
- https://science.thewire.in/feed/
- https://india.mongabay.com/feed/
- https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss
- https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms

## Keywords to filter articles (any match = include)
tiger, leopard, elephant, rhino, lion, wolf, bear,
gharial, crocodile, python, vulture, bustard, dolphin,
wildlife, poaching, forest, sanctuary, reserve, national park,
conservation, species, habitat, corridor, encroachment,
WII, WWF, WTI, forest department

## Known failure modes — handle these explicitly
- RSS feed returns 404 or timeout → log warning, continue with others
- spaCy returns no entities → log as "no location found", skip article
- Nominatim returns result outside India bounds
  (lat < 6 or > 37, lon < 68 or > 98) → reject and skip
- news.json missing or malformed on first run → start with empty list
- GitHub Actions hits Nominatim rate limit → the 1s sleep handles this,
  do not remove it

## V1 Constraints — never violate
- No paid APIs anywhere in this project
- No ANTHROPIC_API_KEY or any API key in code
- No backend server or serverless functions
- Nominatim: always 1 second sleep between calls, always add ", India"
- Never re-process an article URL already in news.json
- GitHub Actions free tier limit: 2000 min/month —
  spaCy model download is the heavy step, cache it with
  actions/cache@v4 keyed on requirements.txt hash
- docs/ folder is what GitHub Pages serves — all frontend files go here

## V1 Build order (for reference — V1 is already built)
1. data/india_pa_gazetteer.csv (at least 200 entries)
2. scripts/requirements.txt
3. scripts/extractor.py
4. scripts/geocoder.py
5. scripts/fetch_and_process.py
6. .github/workflows/fetch_news.yml
7. docs/index.html + docs/map.js + docs/style.css
8. Test locally: python scripts/fetch_and_process.py
   Verify news.json is generated with valid lat/lon entries.

---

# V2 — Ecological Intelligence System (IN BUILD)

All V2 code lives under v2/ directory. Never place V2 files outside v2/.

## Purpose
Detect illegal encroachment, underreported habitat degradation, and corridor
collapse in India — before it appears in news.

## The core intelligence model: Three-Layer Gap Analysis
- Layer 1 (Authorised): PARIVESH forest clearances, NGT orders, eCourts judgments
- Layer 2 (Reported): News events — V1 pipeline + GDELT + Wayback CDX + Kalpavriksh PAU
- Layer 3 (Observed): Global Forest Watch annual loss + GLAD/RADD weekly alerts

Gap signals:
- L3 loss + no L1 clearance = likely illegal encroachment
- L3 loss + no L2 reporting = underreported degradation
- L1 clearance + no L3 loss = clearance reversed or cancelled

## Novel contributions (do not simplify or remove these)
1. Species-constrained toponym disambiguation — score ambiguous place names
   by overlap with IUCN species range map. Patent candidate.
2. Three-layer gap analysis — no prior Indian system cross-references
   regulatory + news + satellite data.
3. eBird specialist:generalist ratio — habitat quality proxy correlated
   with PARIVESH + GFW + news events. Standalone paper candidate.
4. Multi-species Conflict Risk SDM — extends Kitratporn & Takeuchi 2020
   and Chester Zoo/Oxford/WTI 2025 to multi-species, all-India, NLP-curated
   occurrence data using a 10-algorithm ensemble (biomod2).

---

## V2 Build Phases

### Phase 0 — Foundation (CURRENT PHASE)
Status: Gold standard CSV exists (180 rows). Validation in progress.

**Gold standard validation rules:**
- 16 event types: poaching, human-wildlife-conflict, mortality, sighting,
  species-discovery, conservation-action, habitat-threat, policy, research,
  rescue, disease, flood-displacement, wildlife-crime, wildlife-crime-corridor,
  fire, coexistence, other
- Each row needs: event_type, species[], correct_location, is_false_positive,
  duplicate_cluster flags
- TARGET: minimum 50 examples per class before training
- CURRENT PROBLEM: 180 rows across 16 classes = ~11 per class average.
  Underrepresented classes will cause classifier to overfit.
  GDELT expansion to 800+ rows is mandatory before training.
- Track per-class counts during validation. Flag when any class < 10.

**Validation assistant prompt (use this when working through CSV rows):**
```
You are helping validate a gold standard CSV for a wildlife news event
classifier for India. The 16 event types are:
poaching, human-wildlife-conflict, mortality, sighting, species-discovery,
conservation-action, habitat-threat, policy, research, rescue, disease,
flood-displacement, wildlife-crime, wildlife-crime-corridor, fire,
coexistence, other

For each article row I paste, return:
- Suggested label (from the 16 types above)
- Confidence: high / medium / low
- If low: what is ambiguous and what would resolve it
- Flag if row should be excluded (duplicate, non-wildlife, location failure)
- Running count of labels per class — flag any class below 10 examples
Return structured output only. No explanation.
```

**Phase 0 pending tasks (in order):**
- [ ] Validate 180-row gold standard CSV — IN PROGRESS
- [ ] Run GDELT BigQuery query for India wildlife URLs 2013-present
      themes: ENV_WILDLIFE, ENV_POACHING, ENV_DEFORESTATION
- [ ] Expand gold standard to 800+ rows via active learning:
      seed model on 180 rows → pre-label GDELT candidates → correct errors
- [ ] Email Kalpavriksh for Protected Area Update PDF archive
- [ ] Extract corridor metadata from 3 PDFs:
      MoEF 2023 corridor report, WTI "Right of Passage" 2005, WII Tiger Status 2022
      Method: pdfplumber for text layer → structured rows into PostgreSQL
      Corridor polygons: WDPA convex hull between connecting PA pairs (Phase 1)
      Replace with manual QGIS digitizing in Phase 2
- [ ] Contact BirdLife International for India KBA shapefile (kba.iucnredlist.org)

**Spatial reference data to load into PostGIS (Phase 0):**
- Census of India admin boundaries: india_states, india_districts, india_villages
- WDPA India PA boundaries (REST API + monthly shapefile, free)
- IUCN range maps: tiger, elephant, lion, leopard, rhino, gharial, vultures,
  Great Indian Bustard, blackbuck, wolf, florican (for ONE fire cross-check)
- KBA shapefile (pending BirdLife agreement)
- Forest cover boundary: FSI ISFR shapefile (authoritative GoI forest layer)
- Open Natural Ecosystems (ONE) boundary:
  Email NCF (Nature Conservation Foundation) and ATREE (Abi Vanak's group)
  for shapefile directly. Interim: derive from MODIS MCD12Q1 by combining
  grassland + savanna + shrubland classes minus revenue forest boundary.
  Critical layer — do not substitute wasteland atlas for this.
- Agriculture extent: ISRO Bhuvan crop extent + MODIS MCD12Q1 cropland class
- Wasteland boundary: NRSC Wasteland Atlas 2019 (free shapefile download
  from NRSC website). Use only for cross-check with IUCN ranges, not as
  ecological significance filter.
- Forest cover raster: FSI ISFR + GFW annual loss layers
- Above-ground biomass raster: ESA CCI Biomass (100m, free) or
  Spawn et al. 2020 global dataset

### Phase 1 — NLP Pipeline
Build after gold standard reaches 800+ validated rows.

- Species extraction: spaCy NER + custom wildlife entity ruler
- Species-constrained toponym disambiguation:
  Score ambiguous place name candidates by IUCN range map overlap.
  Use PostGIS ST_Intersects(candidate_geometry, species_range_geometry).
- Event classifier: scikit-learn LogisticRegression + TF-IDF baseline,
  upgrade to fine-tuned DistilBERT if F1 < 0.75 per class
- Deduplication: sentence-transformers embeddings, cluster by
  location + species + time window + cosine similarity > 0.85
- Gate: F1 > 0.75 per class required before moving to Phase 2

### Phase 2 — Data Ingestion (Three Tracks)

**Track 1 — News (Reactive, 25-year target coverage):**
- Live RSS: feedparser
- Full article text: trafilatura
- Historical 2013-present: google-cloud-bigquery → GDELT
  (themes: ENV_WILDLIFE, ENV_POACHING, ENV_DEFORESTATION)
- Historical 2003-present: requests → Wayback Machine CDX API
  per major outlet: DTE, Mongabay India, The Hindu, The Wire, NDTV
- Historical 2000-2024: Kalpavriksh PAU PDFs (pdfplumber + pytesseract)
- Pre-2003 gap: Factiva/LexisNexis if institutional access available
  (The Hindu from 1990, Times of India from 1991 in XML export)
- All sources → same NLP pipeline from Phase 1

Coverage density reality — account for this in temporal SDM:
- 2010-present: dense, reliable for most species and states
- 2003-2009: moderate, major outlets only, regional gaps
- Pre-2003: sparse, mainly PAU and institutional archives
- Regional language coverage: near-zero before 2015
- Temporal SDM baselines are reliable from 2010 onward.
  Pre-2010 data useful for trend direction but not absolute calibration.

**Track 2 — Regulatory (Predictive):**
- PARIVESH: datagovindia pip package + direct portal scrape for FC/WL
- NGT + High Courts: ecourts pip package (GPL-3.0)
- District Courts: requests → Akshit eCourts API (free non-commercial)
- Parse: case_number, case_status, forest_area_ha, clearance_type,
  verdict_summary, project_location
- TRAFFIC Wildlife Trade Portal (include in current build):
  Register at wildlifetradeportal.org — immediate access after registration.
  Filter by India + focal species. Export as CSV.
  No public API — build a CSV loader, NOT an API connector.
  Fields: species, product type, seizure location, date, transport method,
  criminal justice outcome.
  Load into traffic_seizures table in PostgreSQL.
  Use seizure locations as occurrence points for wildlife smuggling
  corridor SDM only — separate model pipeline, not combined with HWC models.
- Other wildlife crime databases (POST-PUBLICATION — do not build now):
  C4ADS CWT-ID, Tigernet (NTCA), WCCB — all require formal data agreements.
  Add after V2 is published.

**Track 3 — Spatial/Satellite (Continuous):**
- Global Forest Watch REST API (free)
- Annual tree cover loss 2001-2024 (30m, UMD/Hansen)
- Near-real-time: GLAD-L, GLAD-S2, RADD alerts (weekly, 10-30m)
- Loss by driver: agriculture / fire / urbanization / forestry
- Corridor width + fragmentation: rasterio + scipy on GeoTIFF

**Track 4 — Biological Indicators (DEFERRED):**
- eBird API — specialist:generalist bird ratio per PA/corridor over time
- Defer until Tracks 1-3 are operational

### Phase 3 — Event Store

Database: PostgreSQL + PostGIS + pgvector
Local dev: PostgreSQL 16 on Windows, pgAdmin 4
Production: Hetzner CX32 (~€7.50/month, 8GB RAM)

```sql
events (
  event_id UUID PRIMARY KEY,
  event_type TEXT,
  event_subtype TEXT,
  source_track TEXT,          -- 'news' | 'regulatory' | 'satellite'
  location GEOMETRY(POINT, 4326),
  inside_pa BOOLEAN,
  pa_name TEXT,
  corridor_name TEXT,
  event_date DATE,
  reported_date DATE,
  severity TEXT,
  outcome_summary TEXT,
  embedding VECTOR(384)       -- sentence-transformers output
)

event_species (event_id, species_common, scientific_name, iucn_status, count)
event_articles (event_id, url, headline, source, published)

regulatory (case_number, case_status, forest_area_ha, clearance_type,
            verdict_summary, project_name, location GEOMETRY)

forest_cover (polygon_id, year, loss_ha, loss_driver,
              corridor_width_m, fragmentation_index, alert_type)

forest_fire_events (
  fire_id UUID PRIMARY KEY,
  detection_date DATE,
  location GEOMETRY(POINT, 4326),
  burned_area_ha FLOAT,
  classification TEXT,  -- FOREST_FIRE | ONE_FIRE | AGRICULTURAL_STUBBLE |
                        -- AGRICULTURAL_SUSPICIOUS | WASTELAND_IN_RANGE |
                        -- WASTELAND_OUT_OF_RANGE | UNCLASSIFIED
  biomass_lost_tonnes FLOAT,
  fire_source TEXT,     -- MODIS | VIIRS | Sentinel2
  confidence TEXT,      -- high | nominal | low
  inside_pa BOOLEAN,
  pa_name TEXT,
  corridor_name TEXT,
  iucn_species_overlap TEXT[],
  parivesh_clearance_nearby BOOLEAN,
  encroachment_pattern BOOLEAN
)

-- Research papers (Phase 3 extension — do not build before Phase 1 gate)
research_papers (
  paper_id UUID PRIMARY KEY,
  title TEXT,
  doi TEXT,
  year_published INT,
  species_tags TEXT[],
  spatial_extent GEOMETRY,
  document_type TEXT,         -- 'paper' | 'report' | 'policy'
  embedding VECTOR(384)       -- same pgvector column, different document_type
)
```

Analytics:
- Corridor Stress Index: events/month per corridor (news track)
- Corridor Integrity Index: width + connectivity trend (GFW track)
- Combined signals: high stress + declining integrity = active collapse

### Phase 4 — Intelligence Layer

**RAG Engine:**
- Query event store with structured filters
- Retrieve relevant events as context
- LLM synthesises plain-English report with source citations
- LLM: Groq free tier (Llama 3.1 70B) during dev

**Alerts:**
- Poaching spike in PA → flag
- Same species, multiple deaths, same area < 30 days → flag
- GFW alert in PA buffer + no PARIVESH clearance = illegal encroachment alert
- L3 loss + no L2 news = underreported degradation flag
- PARIVESH clearance in wildlife corridor = predictive threat alert
- Forest fire or ONE fire + adjacent PARIVESH clearance = land conversion alert
- Repeated fire in same location across years outside agriculture = encroachment pattern flag

**Forest Fire Intelligence (Fifth Domain):**
Forest fire is one of the strongest real-time three-layer gap analysis signals:
- L2 news reports fire location and approximate cause
- L3 satellite quantifies burned area and biomass loss precisely
- L1 regulatory cross-check: fire + nearby PARIVESH clearance = arson for
  land clearing signal — documented encroachment tactic in Northeast and
  Central India

Fire classification — CRITICAL:
Never treat all fires as equivalent. Use five reference layers to classify:

Layer 1 — Forest cover boundary (FSI/ISFR):
  Fire inside forest cover = FOREST FIRE
  → Flag immediately, calculate biomass loss, feed corridor integrity index

Layer 2 — Open Natural Ecosystems (ONE) boundary:
  Fire inside ONE but outside forest cover = OPEN ECOSYSTEM FIRE
  → Flag separately — grasslands, savannas, sholas, scrublands, rocky
    outcrops are ecologically primary habitats. NOT wasteland.
  → Cross-check with IUCN range maps: if inside range of grassland
    specialists (Great Indian Bustard, blackbuck, wolf, florican) → high
    priority flag regardless of legal land classification
  → ONEs are routinely targeted for solar farms, plantations, and
    infrastructure because they aren't legally forest. Fire + PARIVESH
    clearance in same ONE location = strong land conversion signal.
  → Data source: NCF/WII ONE maps. Email NCF and ATREE (Abi Vanak's group)
    directly for shapefile. Some ONE extent derivable from MODIS MCD12Q1
    by combining grassland + savanna + shrubland classes minus revenue forest.

Layer 3 — Agriculture extent:
  Fire inside agriculture extent = AGRICULTURAL FIRE
  → Apply seasonal filter:
    Oct-Nov in Indo-Gangetic Plain = stubble burning → EXCLUDE from system
    Other seasons = flag as suspicious (why burning cropland off-season?)
  → Data source: ISRO Bhuvan crop extent, MODIS MCD12Q1 cropland class,
    ICRISAT district agricultural land data, NRSC FASAL programme

Layer 4 — Wasteland boundary (NRSC Wasteland Atlas 2019):
  Fire inside wasteland but NOT inside forest or ONE boundary:
  → Do NOT automatically dismiss as low ecological significance
  → Many pristine habitats are legally classified as wasteland in India
    (grasslands, scrublands, wetland margins, shola edges)
  → Cross-check with IUCN range maps before downgrading priority
  → If outside any species range: log only, low priority
  → If inside species range: treat same as ONE fire

Layer 5 — IUCN range map cross-check (applies to layers 2 and 4):
  Fire in wasteland or ONE + inside IUCN range of any focal species
  → Elevate to high priority regardless of land classification

Classification output per fire event:
  FOREST_FIRE | ONE_FIRE | AGRICULTURAL_STUBBLE | AGRICULTURAL_SUSPICIOUS |
  WASTELAND_IN_RANGE | WASTELAND_OUT_OF_RANGE | UNCLASSIFIED

Only FOREST_FIRE, ONE_FIRE, AGRICULTURAL_SUSPICIOUS, and WASTELAND_IN_RANGE
enter the intelligence system. Others are logged but not flagged.

Biomass loss calculation (for FOREST_FIRE and ONE_FIRE):
- Burned area: MODIS MCD64A1 (monthly, 500m) or VIIRS VNP64A1 (375m)
  For small fires (<1 ha): Sentinel-2 at 10m required — flag limitation
- Above-ground biomass: ESA CCI Biomass raster (100m, free) or
  Spawn et al. 2020 global dataset
- Calculation: burned forest area (ha) × biomass density (t/ha) =
  biomass lost (tonnes)
- Output: "Fire at [location] destroyed approximately X hectares of
  [forest type / grassland type], estimated Y tonnes biomass lost"
- Store in forest_fire_events table with geometry, classification,
  biomass_lost_tonnes, fire_source (MODIS/VIIRS/Sentinel), confidence

Active fire monitoring:
- NASA FIRMS API (free) — active fire alerts within 3-6 hours
- MODIS and VIIRS both available via FIRMS
- Cross-reference active fire location against all 5 layers in real time
- Trigger alert pipeline immediately for FOREST_FIRE and ONE_FIRE detections

Temporal encroachment pattern detection:
- Pixel-wise fire frequency: fires in same location > 2 years consecutively
  outside agricultural season = encroachment pattern flag
- Combine with: PARIVESH applications in same buffer, GFW forest loss,
  news reports of land conflict in same area



**Conflict Risk SDM (Novel — Phase 4 extension):**
References:
- Kitratporn & Takeuchi 2020, Remote Sensing 12:90 — time-calibrated SDM
  using news occurrences + two-axis classification. Extended here to
  multi-species, all-India, NLP-curated occurrence data.
- Chester Zoo / Oxford / WTI 2025, Global Ecology and Conservation —
  ensemble of 10 ML algorithms for HWC mapping in Wayanad. WildLens
  applies this ensemble approach at national scale across multiple species.
- ACM SIGCAS 2022 (dl.acm.org/doi/10.1145/3530190.3534818) — automated
  HWC knowledge base from Indian news articles, 90% classification accuracy.
  WildLens differentiates by adding satellite + regulatory layers and
  25-year multilingual coverage.

Model approach — ENSEMBLE (not single MaxEnt):
Use an ensemble of 10 SDM algorithms as per Chester Zoo/Oxford/WTI 2025.
Ensemble corrects for individual algorithm biases and outperforms single
MaxEnt on accuracy and spatial generalisability.
Algorithms to include:
- MaxEnt (maximum entropy)
- Random Forest
- Gradient Boosting Machine (GBM)
- Generalised Linear Model (GLM)
- Generalised Additive Model (GAM)
- Boosted Regression Trees (BRT)
- Classification and Regression Trees (CART)
- Flexible Discriminant Analysis (FDA)
- Surface Range Envelope (SRE)
- Multivariate Adaptive Regression Splines (MARS)
Implementation: biomod2 R package — standard ensemble SDM framework,
handles all 10 algorithms, produces ensemble probability surface and
variable importance scores across algorithms.
Final output: ensemble weighted mean probability surface per species
per season per year.

Core principle — time calibration (from Kitratporn & Takeuchi 2020):
- Each occurrence point matched to environmental predictors from its specific
  season AND year, not a pooled average. Produces time-independent models
  comparable across years and captures inter-annual variation.
- Build ensemble per species: resource suitability/wet, resource suitability/dry,
  human pressure/wet, human pressure/dry — 4 ensemble runs per species.
- Project each ensemble onto predictors for every year in the event store →
  one conflict probability surface per season per year.

Two-axis classification:
- Axis 1 Resource Suitability: IUCN range overlap + GFW forest cover +
  distance to PA boundary + EVI (MODIS MOD09A1) + KBDI drought index
- Axis 2 Human Pressure: WorldPop population density + OSM road proximity +
  MODIS nighttime lights (DMSP/VIIRS intercalibrated) + distance to PA
- Thresholds: 10th percentile of presence (lower) + maxSS (upper)
- Output zones: High / Likely / Low / Rare / Avoided matrix

Temporal change analysis (key output):
- Pixel-wise linear regression on predicted probability across all years
- Slope = rate and direction of change per pixel per species
- Intercept = baseline conflict probability in first modelled year
- Visualisation: RGB composite (Red=decreasing, Green=baseline, Blue=increasing)
- Interpretable output: "conflict expanding / stable / contracting"
  per corridor per species — feeds directly into corridor stress alerts

Bias correction (mandatory):
- Gaussian kernel density of occurrence locations weighted by deduplicated
  report count per location → rescale 1-20 → sample 10,000 background points

Parameter optimisation:
- biomod2 handles algorithm-specific tuning internally
- k-fold cross-validation (k=5) per algorithm per species
- Ensemble weighting by TSS (True Skill Statistic) per algorithm
- Target ensemble TSS > 0.7 per species before accepting output
- Variable importance scores averaged across all algorithms

Model architecture — CRITICAL:
Each species/conflict type gets its own completely independent model pipeline.
No combined or multi-species models. Ever.
Per species: separate occurrence dataset, separate predictor extraction,
separate bias correction, separate biomod2 ensemble run,
separate output rasters, separate database table for results.
Shared across species: environmental predictor layers, PostGIS spatial
reference data, bias correction method, biomod2 tuning approach.
This means 8 separate model pipelines running independently.

Species and conflict types modelled:
- Elephant HWC (crop raid, human fatality, property damage)
- Tiger HWC (livestock kill, human attack near forest edges)
- Leopard HWC (periurban fringe, scrub-forest boundaries)
- Sloth bear HWC (Northeast + Central India)
- Himalayan black bear HWC (Himachal, Uttarakhand, J&K)
- Sun bear HWC (Northeast India — only if occurrences > 30 per season)
- Poaching hotspots (human pressure axis = road access + ranger station
  proximity + demand centre proximity)
- Wildlife smuggling corridors (occurrence = seizure locations; pressure axis =
  border proximity + transit route density)

NOT modelled as SDM: snakebite. Snakebite is a public health metric driven
by human behaviour, footwear, housing, agriculture — it does not fit the
resource suitability vs human pressure ecological framework and would degrade
the novel contribution's conceptual integrity. Tag snakebite events separately
in the event store as a public health indicator if data exists.

Run schedule:
- Full model rebuild: ANNUALLY — constrained by annual predictor resolution
  (MODIS land cover, WorldPop, nightlights all update once per year)
- Seasonal projection: QUARTERLY — project annual model onto sub-annual
  EVI and KBDI snapshots (both update monthly, valid for seasonal output)
- Do NOT re-run full ensemble quarterly — predictors don't support it

New environmental layers required:
- WorldPop India population grid (100m — worldpop.org, free)
- OSM road network (geofabrik.de, free)
- MODIS nighttime lights DMSP + VIIRS intercalibrated (NASA Earthdata, free)
- KBDI drought index (compute from GSMap precipitation + MTSAT LST)
- EVI from MODIS MOD09A1 (monthly median, gap-fill with 10-year average)
- SRTM terrain roughness index (90m, free)

### Pre-SDM mandatory validation — Coverage Audit
Run before building any SDM model. Gate: SDM build does not start without this.

Coverage audit steps:
1. Plot occurrence density per species per state from the full 25-year corpus
2. Generate a coverage density map — incidents per 100km² per state per species
3. Produce a table: articles per language per state per species
4. Identify coverage gaps explicitly:
   - States with < 10 incidents per species per decade = unreliable SDM baseline
   - Likely gaps: interior Chhattisgarh, Jharkhand, Arunachal, Nagaland, Mizoram
   - Pre-2010 data: treat as trend direction only, not absolute calibration
5. Validate occurrence density against WII published HWC survey data for
   2-3 states where WII ground-truth exists (Kerala, Karnataka, Assam)
   If news-derived occurrence map does not correlate with WII field data,
   this is a limitations section problem — document it, do not ignore it.
6. Regional language coverage is a methodological strength — quantify it:
   show what percentage of incidents are captured only in regional language
   press and would be missed by English-only systems.
   This is a direct differentiator from all prior SDM studies for India.

Output: coverage_audit.md in v2/docs/ before any SDM code is written.

### Field Reporting App — DEFERRED (post-publication only)
Do not build before V2 publication. Reasons:
- False reporting in Indian HWC context is motivated, not random:
  farmers inflate crop damage for compensation, poachers divert ranger
  attention with false sightings, political actors report false encroachment.
- Gaussian kernel density bias correction handles reporting effort bias.
  It does NOT handle motivated false reporting bias. These are different problems.
- Crowd-sourced occurrence data in a published SDM invites reviewer rejection
  on data quality grounds.

If built post-publication, minimum trust architecture required:
- Reporter verification: forest department ID, NGO affiliation, or
  trusted community reporter status. Anonymous reports go into a separate
  unvalidated bucket, never into the SDM.
- Cross-validation gate: field report enters validated event store only if
  corroborated by one of — another reporter within 48 hours, satellite
  imagery, or news coverage within 30 days.
- Species + location plausibility: auto-reject if species falls outside
  IUCN range by more than 50km (toponym disambiguation system handles this).
- Temporal clustering flag: sudden spike of reports from one location
  triggers manual review, not automatic ingestion.


- Map: one pin per event, PA boundaries, corridor stress heat layer,
  SDM conflict risk overlay (species-selectable), seasonal toggle
- Dashboard: top species/PAs, HWC trend by state, corridor stress panel
- Chat: Ask WildLens v2 — RAG-powered, not keyword search
- Export: CSV / GeoJSON

---

## Research Intelligence Layer
Build order: Phase 3 only — gate is Phase 1 classifier F1 > 0.75.

### What this is
An extension of the existing pgvector infrastructure to store embeddings
from peer-reviewed wildlife/ecology papers alongside news event embeddings.
NOT a separate system. Same FastAPI layer, same retrieval pipeline,
document_type column distinguishes papers from events.

### Why it adds value (three specific uses only — no scope beyond these)
1. Species range validation — improve toponym disambiguation beyond static
   IUCN shapefiles, especially for range-shifting species
2. SDM calibration priors — published HWC studies provide training priors
   for the five focal species SDM rather than deriving from scratch
3. Corridor integrity baselines — literature defines what "degraded" means
   per corridor per ecosystem; your system currently has no such benchmark

### Starting corpus (200-300 papers max — do not scale before pipeline works)
- WII technical reports (publicly available)
- WCS India published studies
- Peer-reviewed HWC literature for five focal species
- Western Ghats corridor studies (MoEF 2023, WTI 2005, WII 2022)
- IUCN assessments for focal species

### Ingestion pipeline (when ready)
1. PDF → text: pdfplumber (text layer) or pytesseract (scanned)
2. Chunk at section boundaries — preserve Methods/Results/Discussion
3. Tag species using existing spaCy wildlife entity ruler
4. Tag spatial extent via PostGIS if study area is mentioned
5. Embed with sentence-transformers/all-MiniLM-L6-v2 (free, local, 384-dim)
6. Store in research_papers table
7. Index: CREATE INDEX ON research_papers USING ivfflat (embedding vector_cosine_ops)

---

## Full stack reference

| Layer | Tool | Cost |
|---|---|---|
| Database | PostgreSQL 16 + PostGIS + pgvector | Free |
| NLP | spaCy en_core_web_trf | Free |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Free, local |
| Classifier | scikit-learn → DistilBERT if needed | Free |
| RSS | feedparser | Free |
| Article fetch | trafilatura | Free |
| Historical | GDELT via BigQuery free tier | Free (1TB/month) |
| Wayback | requests → CDX API | Free |
| PARIVESH | datagovindia + direct scrape | Free |
| Courts | ecourts + Akshit API | Free |
| Satellite | GFW REST API + rasterio | Free |
| LLM/RAG | Groq free tier (Llama 3.1 70B) | Free (rate-limited) |
| API layer | FastAPI | Free |
| Dev hosting | Supabase + Render free tier | Free |
| Prod hosting | Hetzner CX32 | ~€7.50/month |
| Active fire alerts | NASA FIRMS API (MODIS + VIIRS) | Free |
| Burned area | MODIS MCD64A1 + VIIRS VNP64A1 | Free |
| Above-ground biomass | ESA CCI Biomass / Spawn et al. 2020 | Free |
| ONE boundary | NCF / ATREE direct request | Free (data agreement) |
| Wasteland boundary | NRSC Wasteland Atlas 2019 | Free |
| Agriculture extent | ISRO Bhuvan + MODIS MCD12Q1 | Free |

---

## Global constraints — never violate
- V1 is live and actively maintained — bug fixes and new features are normal.
  Only touch root and docs/ files for V1 work.
  All V2 work in v2/ directory only.
  Never let V2 dependencies or database connections bleed into V1 files.
- No paid APIs during development.
- Groq free tier is rate-limited — build retry with exponential backoff.
- Nominatim (V1): always 1 second sleep, always append ", India".
- Never hardcode credentials. Use .env + python-dotenv.
- Gold standard CSV is the evaluation benchmark for every pipeline stage.
  Do not train any model without validating against it first.
- Do not build research paper layer before Phase 1 F1 > 0.75.

## Methodological checkpoint — MANDATORY before any build task
Before writing any code for any V2 component, Claude Code must:
1. Present a plain-English summary of the methodology it is about to implement
   — what it does, what data it uses, what assumptions it makes, what the
   output is, and what could go wrong ecologically or statistically.
2. Explicitly flag any assumption that requires domain expertise to validate
   (e.g. species range interpretation, fire classification logic, SDM predictor
   selection, corridor integrity thresholds, biomass calculation method).
3. Ask Nikunj to confirm the methodology is ecologically accurate before
   proceeding.
4. Only start building after explicit confirmation is received.

This checkpoint applies to every new component, every phase transition,
and every time a methodological parameter changes. It does not apply to
bug fixes, UI changes, or non-methodological code tasks.

The reason: WildLens V2 is intended for publication and policy use.
A methodological error caught before building costs nothing.
The same error caught after building costs everything.

---

## Publication targets
- Primary: Methods in Ecology and Evolution
- Framing: domain-expert pipeline where ecological knowledge constrains
  every stage. Evaluated against gold standard.
- Patent consultation after paper acceptance:
  species-constrained toponym disambiguation is the primary candidate.
