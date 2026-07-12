#!/usr/bin/env python3
"""
Regional-language wildlife news pipeline.

Fetches RSS feeds in Malayalam, Hindi, Assamese (and other Indian languages).
Translates headline + description snippet to English, then runs the same
keyword-filter → gazetteer → spaCy → Nominatim pipeline as the English feed.

Outputs: docs/regional/news.json
  Each article carries both the original-language headline AND the English
  translation so the UI can show the original while searching/categorising
  using the English text.

Zero paid APIs:
  - deep-translator uses Google Translate's public endpoint (no key needed)
  - Nominatim geocoding with mandatory 1s delay
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import feedparser
from dateutil import parser as dateparser

sys.path.insert(0, os.path.dirname(__file__))
from extractor import extract_location
from geocoder import geocode

# Reuse keyword matching logic from main pipeline
from fetch_and_process import (
    KEYWORDS, EXCLUDE_KEYWORDS,
    fix_encoding, matches_keywords, parse_date,
    USER_AGENT, fetch_feed,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ── Regional sources ────────────────────────────────────────────────────────
# Each entry: {'url': ..., 'source': ..., 'lang': ..., 'lang_code': ...}
# lang_code follows ISO 639-1 (used by deep-translator / Google Translate)

REGIONAL_SOURCES = [
    # ── Malayalam (Kerala) ──────────────────────────────────────────────────
    # Mathrubhumi — direct RSS broken (invalid XML); GN ml proxy works (41 entries)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+elephant+tiger'
                '+site:mathrubhumi.com&hl=ml-IN&gl=IN&ceid=IN:ml'),
        'source': 'Mathrubhumi',
        'lang': 'Malayalam',
        'lang_code': 'ml',
    },
    # Manorama Online — direct RSS broken; GN ml proxy (100 entries)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+elephant'
                '+site:manoramaonline.com&hl=ml-IN&gl=IN&ceid=IN:ml'),
        'source': 'Manorama Online',
        'lang': 'Malayalam',
        'lang_code': 'ml',
    },
    # Malayalam catch-all — native terms (വന്യജീവി=wildlife, വനം=forest)
    # Keep to 2 broad terms: GN AND-s query words, so 4 specific terms killed all
    # recent hits (13 total / 0 within 60d). Two broad terms → 55 total / 17 recent.
    {
        'url': ('https://news.google.com/rss/search?q=%E0%B4%B5%E0%B4%A8%E0%B5%8D%E0%B4%AF%E0%B4%9C%E0%B5%80%E0%B4%B5%E0%B4%BF+%E0%B4%B5%E0%B4%A8%E0%B4%82'
                '&hl=ml-IN&gl=IN&ceid=IN:ml'),
        'source': 'Malayalam News',
        'lang': 'Malayalam',
        'lang_code': 'ml',
    },

    # ── Hindi (UP, MP, Uttarakhand, HP, Bihar, Rajasthan) ──────────────────
    # Dainik Jagran — direct RSS returns HTML (Cloudflare blocked); GN hi proxy (100 entries)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger+elephant'
                '+site:jagran.com&hl=hi-IN&gl=IN&ceid=IN:hi'),
        'source': 'Dainik Jagran',
        'lang': 'Hindi',
        'lang_code': 'hi',
    },
    # Amar Ujala — direct RSS working (40 entries)
    {
        'url': 'https://www.amarujala.com/rss/india-news.xml',
        'source': 'Amar Ujala',
        'lang': 'Hindi',
        'lang_code': 'hi',
    },
    # Dainik Bhaskar — large Hindi daily covering MP, Rajasthan, Gujarat
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger+elephant'
                '+sanctuary+site:bhaskar.com&hl=hi-IN&gl=IN&ceid=IN:hi'),
        'source': 'Dainik Bhaskar',
        'lang': 'Hindi',
        'lang_code': 'hi',
    },
    # Patrika — direct RSS broken (invalid XML); GN hi proxy (59 entries)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger+elephant'
                '+site:patrika.com&hl=hi-IN&gl=IN&ceid=IN:hi'),
        'source': 'Patrika',
        'lang': 'Hindi',
        'lang_code': 'hi',
    },

    # ── Assamese (Assam / Northeast) ────────────────────────────────────────
    # Pratidin Time — /feed/ and /rss return English content; broad GN Assamese search (6 entries)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+elephant'
                '+kaziranga+manas&hl=as&gl=IN&ceid=IN:as'),
        'source': 'Pratidin Time',
        'lang': 'Assamese',
        'lang_code': 'as',
    },
    # Asomiya Pratidin — /feed/ was 404; /rss works (50 Assamese entries)
    {
        'url': 'https://asomiyapratidin.in/rss',
        'source': 'Asomiya Pratidin',
        'lang': 'Assamese',
        'lang_code': 'as',
    },

    # ── Telugu (Andhra Pradesh / Telangana) ──────────────────────────────────
    # Sakshi — direct RSS works (10 entries)
    {
        'url': 'https://www.sakshi.com/rss.xml',
        'source': 'Sakshi',
        'lang': 'Telugu',
        'lang_code': 'te',
    },
    # Eenadu via Google News — te-IN gives more results than en-IN
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:eenadu.net'
                '&hl=te-IN&gl=IN&ceid=IN:te'),
        'source': 'Eenadu',
        'lang': 'Telugu',
        'lang_code': 'te',
    },
    # Telugu catch-all — 2 broad native terms (వన్యప్రాణి=wildlife, అడవి=forest)
    # 3-term version gave 27/7 recent; 2 broad terms → 55/15. GN AND-s terms.
    {
        'url': ('https://news.google.com/rss/search?q=%E0%B0%B5%E0%B0%A8%E0%B1%8D%E0%B0%AF%E0%B0%AA%E0%B1%8D%E0%B0%B0%E0%B0%BE%E0%B0%A3%E0%B0%BF+%E0%B0%85%E0%B0%A1%E0%B0%B5%E0%B0%BF'
                '&hl=te-IN&gl=IN&ceid=IN:te'),
        'source': 'Telugu News',
        'lang': 'Telugu',
        'lang_code': 'te',
    },

    # ── Kannada (Karnataka) ──────────────────────────────────────────────────
    # Prajavani — direct RSS works (50 entries)
    {
        'url': 'https://www.prajavani.net/feed/',
        'source': 'Prajavani',
        'lang': 'Kannada',
        'lang_code': 'kn',
    },
    # Vijay Karnataka — en-IN gives 7 entries; kn-IN gives 0 so keep en-IN
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:vijaykarnataka.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Vijay Karnataka',
        'lang': 'Kannada',
        'lang_code': 'kn',
    },

    # ── Odia (Odisha) ─────────────────────────────────────────────────────────
    # Dharitri — direct RSS works (100 entries)
    {
        'url': 'https://www.dharitri.com/feed/',
        'source': 'Dharitri',
        'lang': 'Odia',
        'lang_code': 'or',
    },
    # Sambad — consistently returns 0 on GN regardless of lang; kept as low-cost probe
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:sambad.in'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Sambad',
        'lang': 'Odia',
        'lang_code': 'or',
    },

    # ── Bengali (West Bengal / Tripura) ──────────────────────────────────────
    # Anandabazar Patrika — en-IN returned 0; bn-IN gives 31 entries
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:anandabazar.com'
                '&hl=bn-IN&gl=IN&ceid=IN:bn'),
        'source': 'Anandabazar Patrika',
        'lang': 'Bengali',
        'lang_code': 'bn',
    },
    # Sangbad Pratidin — en-IN returned 0; bn-IN gives 11 entries
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:sangbadpratidin.in'
                '&hl=bn-IN&gl=IN&ceid=IN:bn'),
        'source': 'Sangbad Pratidin',
        'lang': 'Bengali',
        'lang_code': 'bn',
    },

    # ── Marathi (Maharashtra) ─────────────────────────────────────────────────
    # Loksatta — site-specific query was returning 0; native-term catch-all works better
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:loksatta.com'
                '&hl=mr-IN&gl=IN&ceid=IN:mr'),
        'source': 'Loksatta',
        'lang': 'Marathi',
        'lang_code': 'mr',
    },
    # Maharashtra Times
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:maharashtratimes.com'
                '&hl=mr-IN&gl=IN&ceid=IN:mr'),
        'source': 'Maharashtra Times',
        'lang': 'Marathi',
        'lang_code': 'mr',
    },
    # Sakal — direct RSS working
    {
        'url': 'https://www.sakal.com/feed/',
        'source': 'Sakal',
        'lang': 'Marathi',
        'lang_code': 'mr',
    },
    # Marathi catch-all — native-language terms (वन्यजीव=wildlife, वाघ=tiger, हत्ती=elephant, अभयारण्य=sanctuary)
    # No site: restriction so it pulls from any indexed Marathi source
    {
        'url': ('https://news.google.com/rss/search?q=%E0%A4%B5%E0%A4%A8%E0%A5%8D%E0%A4%AF%E0%A4%9C%E0%A5%80%E0%A4%B5+%E0%A4%B5%E0%A4%BE%E0%A4%98+%E0%A4%B9%E0%A4%A4%E0%A5%8D%E0%A4%A4%E0%A5%80+%E0%A4%85%E0%A4%AD%E0%A4%AF%E0%A4%BE%E0%A4%B0%E0%A4%A3%E0%A5%8D%E0%A4%AF'
                '&hl=mr-IN&gl=IN&ceid=IN:mr'),
        'source': 'Marathi News',
        'lang': 'Marathi',
        'lang_code': 'mr',
    },

    # ── Tamil (Tamil Nadu / Puducherry) ───────────────────────────────────────
    # Dinamalar
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:dinamalar.com'
                '&hl=ta-IN&gl=IN&ceid=IN:ta'),
        'source': 'Dinamalar',
        'lang': 'Tamil',
        'lang_code': 'ta',
    },
    # Dinakaran — separate Tamil daily, South TN coverage
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+sanctuary+site:dinakaran.com'
                '&hl=ta-IN&gl=IN&ceid=IN:ta'),
        'source': 'Dinakaran',
        'lang': 'Tamil',
        'lang_code': 'ta',
    },
    # Tamil catch-all — 2 broad native terms (வனவிலங்கு=wildlife, காடு=forest)
    # 4-term version gave 43 total but only 1 recent; 2 broad terms → 77/6. GN AND-s terms.
    {
        'url': ('https://news.google.com/rss/search?q=%E0%AE%B5%E0%AE%A9%E0%AE%B5%E0%AE%BF%E0%AE%B2%E0%AE%99%E0%AF%8D%E0%AE%95%E0%AF%81+%E0%AE%95%E0%AE%BE%E0%AE%9F%E0%AF%81'
                '&hl=ta-IN&gl=IN&ceid=IN:ta'),
        'source': 'Tamil News',
        'lang': 'Tamil',
        'lang_code': 'ta',
    },

    # ── Gujarati (Gujarat) ────────────────────────────────────────────────────
    # Divya Bhaskar — gu-IN locale
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+lion'
                '+elephant+poaching+sanctuary+site:divyabhaskar.co.in'
                '&hl=gu-IN&gl=IN&ceid=IN:gu'),
        'source': 'Divya Bhaskar',
        'lang': 'Gujarati',
        'lang_code': 'gu',
    },
    # Gujarat Samachar
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+lion'
                '+elephant+sanctuary+site:gujaratsamachar.com'
                '&hl=gu-IN&gl=IN&ceid=IN:gu'),
        'source': 'Gujarat Samachar',
        'lang': 'Gujarati',
        'lang_code': 'gu',
    },
    # Gujarati catch-all — 2 broad native terms (વન્યજીવ=wildlife, જંગલ=forest)
    # 4-term version gave only 3 total; 2 broad terms → 59/21. GN AND-s terms.
    {
        'url': ('https://news.google.com/rss/search?q=%E0%AA%B5%E0%AA%A8%E0%AB%8D%E0%AA%AF%E0%AA%9C%E0%AB%80%E0%AA%B5+%E0%AA%9C%E0%AA%82%E0%AA%97%E0%AA%B2'
                '&hl=gu-IN&gl=IN&ceid=IN:gu'),
        'source': 'Gujarati News',
        'lang': 'Gujarati',
        'lang_code': 'gu',
    },
    # Bengali catch-all — 2 broad native terms (বন্যপ্রাণী=wildlife, বন=forest)
    # Bengali had no native catch-all before (site queries only); 2 broad terms → 96/39.
    {
        'url': ('https://news.google.com/rss/search?q=%E0%A6%AC%E0%A6%A8%E0%A7%8D%E0%A6%AF%E0%A6%AA%E0%A7%8D%E0%A6%B0%E0%A6%BE%E0%A6%A3%E0%A7%80+%E0%A6%AC%E0%A6%A8'
                '&hl=bn-IN&gl=IN&ceid=IN:bn'),
        'source': 'Bengali News',
        'lang': 'Bengali',
        'lang_code': 'bn',
    },
]

REGIONAL_JSON = os.path.join(
    os.path.dirname(__file__), '..', 'docs', 'regional', 'news.json'
)
INDIA_CENTER = (20.5937, 78.9629)

# ── Translation helpers ──────────────────────────────────────────────────────

_translator = None

def _get_translator():
    global _translator
    if _translator is not None:
        return _translator
    try:
        from deep_translator import GoogleTranslator
        _translator = GoogleTranslator
        logger.info('deep-translator loaded OK')
    except ImportError:
        logger.warning('deep-translator not installed — translation skipped')
        _translator = False
    return _translator


def translate_to_english(text: str, src_lang: str) -> str:
    """
    Translate text from src_lang to English using Google Translate (free).
    Returns original text unchanged if translation fails or library missing.
    Rate-limit: deep-translator does NOT enforce its own delay, so callers
    must handle pacing. We add a short sleep after each translation call.
    """
    if not text or not text.strip():
        return text
    Translator = _get_translator()
    if not Translator:
        return text
    try:
        result = Translator(source=src_lang, target='en').translate(text[:500])
        return result if result else text
    except Exception as e:
        logger.debug(f'Translation failed ({src_lang}→en): {e}')
        return text


# ── Article deduplication ────────────────────────────────────────────────────

def load_existing():
    try:
        with open(REGIONAL_JSON, encoding='utf-8') as f:
            raw = f.read()
    except FileNotFoundError:
        logger.info('regional/news.json not found — starting fresh')
        return []

    if '<<<<<<< ' in raw or '=======' in raw or '>>>>>>> ' in raw:
        raise RuntimeError(
            'regional/news.json contains git merge-conflict markers. '
            'Resolve before running the pipeline.'
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f'regional/news.json is corrupted (JSONDecodeError: {e}). '
            'Restore from git before running the pipeline.'
        ) from e

    if not isinstance(data, list):
        raise RuntimeError('regional/news.json root element is not a list — file is malformed.')

    return data


# ── Main pipeline ────────────────────────────────────────────────────────────

def main():
    existing = load_existing()
    seen_urls = {a['url'] for a in existing}
    logger.info(f'Loaded {len(existing)} existing regional articles')

    new_articles = []

    for src in REGIONAL_SOURCES:
        feed_url   = src['url']
        source     = src['source']
        lang       = src['lang']
        lang_code  = src['lang_code']

        logger.info(f'Fetching [{lang}] {source} — {feed_url[:70]}')
        entries = fetch_feed(feed_url)

        for entry in entries:
            url = getattr(entry, 'link', None)
            if not url or url in seen_urls:
                continue

            # Raw (original language) text
            title_raw = fix_encoding(getattr(entry, 'title', '') or '')
            desc_raw  = fix_encoding(getattr(entry, 'summary', '') or '')

            if not title_raw:
                continue

            # ── Translate to English for keyword filtering + location NER ──
            title_en = translate_to_english(title_raw, lang_code)
            desc_en  = translate_to_english(desc_raw[:300], lang_code)
            # Small delay to respect Google Translate's informal rate limit
            time.sleep(0.3)

            # Skip if English title is empty after translation
            if not title_en or not title_en.strip():
                continue

            # ── Keyword filter (on translated English text) ────────────────
            if not matches_keywords(title_en, desc_en):
                continue

            pub_date = parse_date(entry)

            # ── Location extraction (translated English text) ──────────────
            place_name, lat, lon = extract_location(title_en, desc_en)

            if place_name is None:
                logger.debug(f'No location: {title_en[:60]}')
                continue

            if lat is None or lon is None:
                coords = geocode(place_name)
                if coords is None:
                    logger.debug(f'Geocoding failed: {place_name}')
                    continue
                lat, lon = coords

            # Reject generic India-centre pin
            if abs(lat - INDIA_CENTER[0]) < 0.01 and abs(lon - INDIA_CENTER[1]) < 0.01:
                continue

            article = {
                'headline':    title_raw.strip(),   # original language (shown in popup)
                'headline_en': title_en.strip(),     # English (used for search)
                'url':         url,
                'source':      source,
                'lang':        lang,
                'published':   pub_date,
                'place_name':  place_name,
                'lat':         lat,
                'lon':         lon,
            }
            new_articles.append(article)
            seen_urls.add(url)
            logger.info(f'  + [{lang}] {title_en[:55]} @ {place_name}')

    merged = existing + new_articles
    merged.sort(key=lambda a: a.get('published', ''), reverse=True)

    # No pruning — articles are kept indefinitely. The frontend 60-day toggle
    # controls what is visible to users; older articles are accessible via
    # "Show beyond 60 days" without being deleted from the JSON.

    if existing and len(merged) < len(existing) * 0.80:
        raise RuntimeError(
            f'SAFETY ABORT: merged count {len(merged)} is more than 20% below '
            f'existing count {len(existing)}. Not writing regional/news.json.'
        )

    os.makedirs(os.path.dirname(REGIONAL_JSON), exist_ok=True)
    with open(REGIONAL_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info(
        f'Wrote {len(merged)} regional articles to docs/regional/news.json '
        f'({len(new_articles)} new)'
    )


if __name__ == '__main__':
    main()
