"""
WildLens v2 — Gold Standard Validation Tool

Run:
    streamlit run v2/tools/validate.py

Install:
    pip install streamlit pandas trafilatura requests
"""

import html
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import trafilatura

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).resolve().parent.parent.parent
CSV_PATH  = BASE / "v2" / "data" / "gold_standard_annotations.csv"
GAZETTEER = BASE / "data" / "india_pa_gazetteer.csv"

# ─── Constants ────────────────────────────────────────────────────────────────
EVENT_TYPES = [
    "poaching", "hwc", "mortality", "sighting", "species-discovery",
    "conservation-action", "habitat-threat", "mining", "policy", "research",
    "rescue", "disease", "flood-displacement", "wildlife-crime",
    "wildlife-crime-corridor", "fire", "coexistence", "other",
]

CSV_COLS = [
    "event_id", "headline", "url", "source", "published",
    "v1_place_name", "v1_lat", "v1_lon",
    "valid_wildlife_article", "event_type", "event_subtype",
    "species_common", "species_scientific", "species_iucn", "animal_count",
    "correct_place_name", "correct_lat", "correct_lon",
    "location_precision", "location_correct", "location_error_type",
    "human_casualties", "human_injuries", "animal_casualties",
    "severity", "cluster_id", "notes_for_nikunj",
]

# ─── Data helpers ─────────────────────────────────────────────────────────────

def load_csv() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH, dtype=str).fillna("")


def save_csv(df: pd.DataFrame) -> None:
    df.to_csv(CSV_PATH, index=False)



@st.cache_data(show_spinner=False)
def load_gazetteer() -> pd.DataFrame:
    return pd.read_csv(GAZETTEER, dtype=str)


def gaz_search(query: str, gaz: pd.DataFrame) -> pd.DataFrame:
    if not query or len(query) < 2:
        return pd.DataFrame()
    mask = gaz["name"].str.contains(query, case=False, na=False)
    return gaz[mask].head(10)


# ─── Article fetch ────────────────────────────────────────────────────────────

def fetch_article(url: str) -> tuple[str, bool]:
    """Returns (text, success). Caches in session_state.article_cache."""
    if url in st.session_state.article_cache:
        return st.session_state.article_cache[url]
    try:
        raw = trafilatura.fetch_url(url)
        if raw:
            text = trafilatura.extract(raw, include_comments=False, include_tables=False)
            if text and len(text) > 80:
                result = (text, True)
                st.session_state.article_cache[url] = result
                return result
    except Exception:
        pass
    result = ("", False)
    st.session_state.article_cache[url] = result
    return result


# ─── Geocoding ────────────────────────────────────────────────────────────────

def nominatim_search(query: str) -> list[dict]:
    """Returns up to 5 results from Nominatim with 1s delay (ToS)."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{query.strip()}, India",
                "format": "json",
                "limit": 5,
                "countrycodes": "in",
            },
            headers={"User-Agent": "wildlens-v2-validator/1.0"},
            timeout=8,
        )
        time.sleep(1)
        return [
            {
                "name": x["display_name"],
                "lat": float(x["lat"]),
                "lon": float(x["lon"]),
            }
            for x in r.json()
        ]
    except Exception:
        return []


# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WildLens v2 Validator",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.article-box {
    font-size: 14px;
    line-height: 1.75;
    color: #1e293b;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px 24px;
    height: 560px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: Georgia, serif;
}
.meta-box {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    line-height: 1.6;
}
.class-row { font-size: 12px; margin: 1px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Bootstrap session state ──────────────────────────────────────────────────

if "initialized" not in st.session_state:
    st.session_state.df           = load_csv()
    st.session_state.pos          = 0
    st.session_state.show         = "Unvalidated"
    st.session_state.article_cache: dict[str, tuple[str, bool]] = {}
    st.session_state.nom_results: list[dict] = []
    st.session_state.prev_row_idx = -1
    st.session_state.nav_history  = []   # stack of df row indices visited
    st.session_state.initialized  = True

df = st.session_state.df


# ─── Index list (filtered) ────────────────────────────────────────────────────

def get_indices(show: str) -> list[int]:
    if show == "Unvalidated":
        return df.index[df["valid_wildlife_article"].str.strip() == ""].tolist()
    return list(df.index)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🦁 WildLens Validator")

    show = st.radio(
        "Show",
        ["Unvalidated", "All"],
        index=["Unvalidated", "All"].index(st.session_state.show),
        horizontal=True,
        key="_show_radio",
    )
    if show != st.session_state.show:
        st.session_state.show = show
        st.session_state.pos  = 0

    indices = get_indices(st.session_state.show)
    total   = len(indices)
    pos     = min(st.session_state.pos, max(0, total - 1))
    st.session_state.pos = pos

    st.divider()

    # Progress across all rows
    n_done  = (df["valid_wildlife_article"].str.strip() != "").sum()
    n_total = len(df)
    st.metric("Progress", f"{n_done} / {n_total} validated")
    st.progress(int(n_done) / max(int(n_total), 1))

    # Jump-to input
    if total > 0:
        jump = st.number_input(
            f"Jump to (1–{total})", min_value=1, max_value=total,
            value=pos + 1, step=1, key="_jump",
        )
        if jump - 1 != pos:
            st.session_state.pos = jump - 1
            st.rerun()

    st.divider()

    # Per-class count
    st.caption("Event type counts (red = < 10)")
    type_counts = (
        df[df["event_type"].str.strip() != ""]["event_type"]
        .value_counts()
        .to_dict()
    )
    for et in EVENT_TYPES:
        cnt = type_counts.get(et, 0)
        colour = "🔴" if cnt < 10 else "🟢"
        st.markdown(
            f'<div class="class-row">{colour} <b>{et}</b> — {cnt}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    if st.button("↺ Reload CSV", use_container_width=True):
        st.session_state.df = load_csv()
        st.rerun()


# ─── Guard ────────────────────────────────────────────────────────────────────

if not indices:
    if st.session_state.show == "Unvalidated":
        st.success("🎉 All articles are validated!")
    else:
        st.info("No articles found.")
    st.stop()

idx = indices[pos]
row = df.iloc[idx]

# Detect article change → clear Nominatim results
if st.session_state.prev_row_idx != idx:
    st.session_state.nom_results  = []
    st.session_state.prev_row_idx = idx


# ─── Main layout ──────────────────────────────────────────────────────────────

left, right = st.columns([4, 6])

# ════════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — validation controls
# ════════════════════════════════════════════════════════════════════════════════
with left:
    n_done = (df["valid_wildlife_article"].str.strip() != "").sum()
    st.markdown(f"### {row['event_id']} &nbsp;·&nbsp; #{idx + 1} of {len(df)} &nbsp;·&nbsp; {n_done} validated", unsafe_allow_html=True)
    st.caption(f"**{row['source']}** · {row['published']}")
    st.markdown(f"**{row['headline']}**")

    st.divider()

    # ── Validity ──────────────────────────────────────────────────────────────
    st.markdown("**Valid wildlife article?**")
    v_opts  = ["YES", "NO — False Positive", "DUPLICATE"]
    raw_val = row["valid_wildlife_article"].strip()
    if raw_val == "YES":
        v_def = 0
    elif raw_val in ("NO", "NO — False Positive"):
        v_def = 1
    elif raw_val == "DUPLICATE":
        v_def = 2
    else:
        v_def = 0

    validity = st.radio(
        "Validity", v_opts, index=v_def,
        horizontal=True, label_visibility="collapsed",
        key=f"valid_{idx}",
    )

    # ── Event type ────────────────────────────────────────────────────────────
    st.markdown("**Event type**")
    cur_et  = row["event_type"].strip()
    et_idx  = EVENT_TYPES.index(cur_et) if cur_et in EVENT_TYPES else len(EVENT_TYPES) - 1
    event_type = st.selectbox(
        "Event type", EVENT_TYPES, index=et_idx,
        label_visibility="collapsed",
        key=f"etype_{idx}",
    )

    st.divider()

    # ── Location ──────────────────────────────────────────────────────────────
    st.markdown("**Location**")
    v1_place = row["v1_place_name"] or "—"
    v1_lat   = row["v1_lat"] or "—"
    v1_lon   = row["v1_lon"] or "—"
    st.caption(f"V1 detected: **{v1_place}** ({v1_lat}, {v1_lon})")

    def_place = row["correct_place_name"] or row["v1_place_name"] or ""
    def_lat   = row["correct_lat"]   or row["v1_lat"]   or ""
    def_lon   = row["correct_lon"]   or row["v1_lon"]   or ""

    # Override values set by "Use" buttons — read before widgets are instantiated.
    # Must also delete the widget's existing session_state key so Streamlit
    # respects the new value= parameter rather than ignoring it.
    if f"place_{idx}_pending" in st.session_state:
        def_place = st.session_state.pop(f"place_{idx}_pending")
        st.session_state.pop(f"place_{idx}", None)
    if f"lat_{idx}_pending" in st.session_state:
        def_lat = st.session_state.pop(f"lat_{idx}_pending")
        st.session_state.pop(f"lat_{idx}", None)
    if f"lon_{idx}_pending" in st.session_state:
        def_lon = st.session_state.pop(f"lon_{idx}_pending")
        st.session_state.pop(f"lon_{idx}", None)

    place_name = st.text_input(
        "Correct place name", value=def_place,
        key=f"place_{idx}",
    )
    c1, c2 = st.columns(2)
    with c1:
        lat_str = st.text_input("Lat", value=def_lat, key=f"lat_{idx}")
    with c2:
        lon_str = st.text_input("Lon", value=def_lon, key=f"lon_{idx}")

    # ── Gazetteer search ──────────────────────────────────────────────────────
    with st.expander("🔍 Gazetteer — search PAs / reserves"):
        gaz      = load_gazetteer()
        gaz_q    = st.text_input(
            "Search (e.g. Corbett, Kaziranga)", key=f"gazq_{idx}",
        )
        gaz_hits = gaz_search(gaz_q, gaz)
        if not gaz_hits.empty:
            for _, gr in gaz_hits.iterrows():
                ga, gb = st.columns([4, 1])
                with ga:
                    st.markdown(f"`{gr['name']}` — *{gr.get('type', '')}*")
                with gb:
                    if st.button("Use", key=f"guz_{idx}_{gr['name']}"):
                        st.session_state[f"place_{idx}_pending"] = gr["name"]
                        st.session_state[f"lat_{idx}_pending"]   = str(gr["lat"])
                        st.session_state[f"lon_{idx}_pending"]   = str(gr["lon"])
                        st.rerun()

    # ── Nominatim search ──────────────────────────────────────────────────────
    with st.expander("🌐 Nominatim geocoder"):
        nom_q = st.text_input(
            "Search query", value=place_name, key=f"nomq_{idx}",
        )
        if st.button("Search Nominatim", key=f"nomsearch_{idx}"):
            with st.spinner("Searching…"):
                st.session_state.nom_results = nominatim_search(nom_q)
            if not st.session_state.nom_results:
                st.warning("No results found.")

        for i, res in enumerate(st.session_state.nom_results):
            na, nb = st.columns([5, 1])
            with na:
                st.markdown(
                    f"<small>{html.escape(res['name'])}</small> "
                    f"· `{res['lat']:.4f}, {res['lon']:.4f}`",
                    unsafe_allow_html=True,
                )
            with nb:
                if st.button("Use", key=f"nom_{idx}_{i}"):
                    short = res["name"].split(",")[0].strip()
                    st.session_state[f"place_{idx}_pending"] = short
                    st.session_state[f"lat_{idx}_pending"]   = f"{res['lat']:.5f}"
                    st.session_state[f"lon_{idx}_pending"]   = f"{res['lon']:.5f}"
                    st.session_state.nom_results = []
                    st.rerun()

    # ── Mini map ──────────────────────────────────────────────────────────────
    try:
        lat_f = float(st.session_state.get(f"lat_{idx}", lat_str) or lat_str)
        lon_f = float(st.session_state.get(f"lon_{idx}", lon_str) or lon_str)
        if 6.0 <= lat_f <= 37.0 and 68.0 <= lon_f <= 98.0:
            st.map(
                pd.DataFrame({"lat": [lat_f], "lon": [lon_f]}),
                zoom=6,
                use_container_width=True,
            )
    except (ValueError, TypeError):
        pass

    st.divider()

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes = st.text_area(
        "Notes", value=row["notes_for_nikunj"],
        height=72, key=f"notes_{idx}",
    )

    st.divider()

    # ── Save helper ───────────────────────────────────────────────────────────
    def collect_and_save() -> None:
        v_raw  = st.session_state.get(f"valid_{idx}", validity)
        val_clean = v_raw.split(" —")[0].strip()   # "NO — False Positive" → "NO"

        p_val  = st.session_state.get(f"place_{idx}", place_name)
        la_val = st.session_state.get(f"lat_{idx}",   lat_str)
        lo_val = st.session_state.get(f"lon_{idx}",   lon_str)

        loc_changed = (
            p_val.strip() != (row["v1_place_name"] or "").strip()
            or la_val.strip() != (row["v1_lat"] or "").strip()
        )

        updates = {
            "valid_wildlife_article": val_clean,
            "event_type":             st.session_state.get(f"etype_{idx}", event_type),
            "correct_place_name":     p_val,
            "correct_lat":            la_val,
            "correct_lon":            lo_val,
            "location_correct":       "NO" if loc_changed else "YES",
            "notes_for_nikunj":       st.session_state.get(f"notes_{idx}", notes),
        }
        for col, val in updates.items():
            st.session_state.df.at[idx, col] = val
        save_csv(st.session_state.df)

    # ── Action buttons ────────────────────────────────────────────────────────
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        has_history = len(st.session_state.nav_history) > 0
        if st.button("← Prev", use_container_width=True, disabled=not has_history):
            target_idx = st.session_state.nav_history.pop()
            # Find target in the full "All" index list so we never lose it
            all_indices = list(df.index)
            if target_idx in all_indices:
                st.session_state.show = "All"
                st.session_state.pos  = all_indices.index(target_idx)
            st.rerun()
    with b2:
        if st.button("Skip →", use_container_width=True, disabled=(pos >= total - 1)):
            st.session_state.nav_history.append(idx)
            st.session_state.pos = pos + 1
            st.rerun()
    with b3:
        if st.button("💾 Save", use_container_width=True):
            collect_and_save()
            st.toast("Saved!", icon="✅")
    with b4:
        if st.button("Save & Next", type="primary", use_container_width=True):
            st.session_state.nav_history.append(idx)
            collect_and_save()
            # In "Unvalidated" view, the saved article drops out of the list
            # automatically — pos already points to the next one. Only increment
            # pos in "All" view where the article stays in the list.
            if st.session_state.show == "All" and pos < total - 1:
                st.session_state.pos = pos + 1
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — article reader
# ════════════════════════════════════════════════════════════════════════════════
with right:
    url = row["url"]

    # Fetch (uses cache; won't re-fetch on every rerun)
    if url not in st.session_state.article_cache:
        with st.spinner("Fetching article…"):
            fetch_article(url)

    text, full_ok = st.session_state.article_cache.get(url, ("", False))

    # Status bar + open link
    sc1, sc2 = st.columns([6, 1])
    with sc1:
        if full_ok:
            st.success("Full article loaded via trafilatura")
        else:
            st.warning("Could not fetch full text — headline & metadata shown below")
    with sc2:
        st.markdown(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;padding:6px 12px;background:#1d4ed8;'
            f'color:#fff;border-radius:6px;font-size:13px;text-decoration:none;'
            f'font-weight:600;">Open ↗</a>',
            unsafe_allow_html=True,
        )

    # Article content
    if full_ok:
        escaped = html.escape(text)
        st.markdown(
            f'<div class="article-box">{escaped}</div>',
            unsafe_allow_html=True,
        )
    else:
        fallback = (
            f"Headline: {html.escape(row['headline'])}\n\n"
            f"Source:    {html.escape(row['source'])}\n"
            f"Published: {html.escape(row['published'])}\n"
            f"V1 place:  {html.escape(row['v1_place_name'])} "
            f"({html.escape(row['v1_lat'])}, {html.escape(row['v1_lon'])})\n\n"
            "─────────────────────────────────────────────\n"
            "Full article text could not be fetched.\n"
            "This is common for paywalled, login-required, or\n"
            "JavaScript-rendered pages.\n\n"
            "Click 'Open ↗' to read the article in your browser."
        )
        st.markdown(
            f'<div class="article-box">{fallback}</div>',
            unsafe_allow_html=True,
        )
