#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import feedparser
from dateutil import parser as dateparser

sys.path.insert(0, os.path.dirname(__file__))
from extractor import extract_location
from geocoder import geocode

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

SOURCES = [
    # NOTE: Down to Earth — HTTP 403, blocks all RSS programmatic access.
    # NOTE: thewire.in/feed/ returns 0 entries; science.thewire.in/feed/ is the working endpoint.

    # Mongabay India — wildlife / forests (best Indian wildlife source)
    'https://india.mongabay.com/feed/',
    # Research Matters — Indian science & ecology research
    'https://researchmatters.in/rss.xml',
    # The Wire Science — 25 entries, strong wildlife/ecology coverage
    'https://science.thewire.in/feed/',
    # The Wire Environment — dedicated env feed from Wire tech team; broader climate/policy coverage
    'https://feeds.thewire.in/environment.xml',
    # NDTV — GN search; direct RSS (feedburner) returns 0 wildlife articles
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+elephant+tiger'
                '+poaching+sanctuary+site:ndtv.com&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'NDTV',
    },
    # Indian Express India — wildlife, poaching, forest coverage
    'https://indianexpress.com/section/india/feed/',
    # The Hindu — environment & sci-tech
    'https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss',
    # The Hindu — national news (catches forest fires, poaching, PA stories)
    'https://www.thehindu.com/news/national/feeder/default.rss',
    # The Hindu — other states (northeast, hill states, etc.)
    'https://www.thehindu.com/news/national/other-states/feeder/default.rss',
    # The Hindu — state-specific (major biodiversity states)
    'https://www.thehindu.com/news/national/kerala/feeder/default.rss',
    'https://www.thehindu.com/news/national/karnataka/feeder/default.rss',
    'https://www.thehindu.com/news/national/andhra-pradesh/feeder/default.rss',
    'https://www.thehindu.com/news/national/telangana/feeder/default.rss',
    'https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss',
    # Times of India — environment / wildlife section
    'https://timesofindia.indiatimes.com/rssfeeds/2647163.cms',
    # Times of India — India news (catches forest, wildlife stories)
    'https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms',

    # ── Northeast India ────────────────────────────────────────────────────────
    # Assam Tribune — direct feed blocked (301/403); GN search gives 28/30 kw-pass
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+elephant+tiger'
                '+rhino+kaziranga+poaching+site:assamtribune.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Assam Tribune',
    },
    # Northeast Now — /environment/feed (5/10 kw-pass) vs general /feed (0/10)
    'https://nenow.in/environment/feed',
    # EastMojo — dedicated environment section; covers NE wildlife, species discoveries, conservation
    'https://eastmojo.com/environment/feed/',

    # ── J&K & Ladakh ──────────────────────────────────────────────────────────
    # Greater Kashmir — J&K's largest English daily; Dachigam, Hangul, snow leopard
    # General /feed/ caused PA-name false positives (e.g. taekwondo in Kishtwar)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+snow+leopard'
                '+hangul+sanctuary+dachigam+poaching+site:greaterkashmir.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Greater Kashmir',
    },
    # Rising Kashmir — direct feed returns 0 wildlife (all political); GN search targets hangul/snow leopard
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+snow+leopard'
                '+hangul+sanctuary+site:risingkashmir.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Rising Kashmir',
    },
    # Daily Excelsior — Jammu-based; covers Trikuta hills, Ramnagar, Chenab valley forests
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+snow+leopard'
                '+elephant+poaching+sanctuary+site:dailyexcelsior.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Daily Excelsior',
    },

    # ── UP & MP (Central India tiger belt) ────────────────────────────────────
    # The Pioneer — Lucknow-based; covers Dudhwa, Pilibhit (UP) + Kanha, Bandhavgarh (MP)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:dailypioneer.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'The Pioneer',
    },
    # Central Chronicle — Bhopal-based; dedicated MP coverage (Satpura, Pench, Panna)
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:centralchronicle.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Central Chronicle',
    },

    # ── Himachal Pradesh & Uttarakhand ────────────────────────────────────────
    # Hill Post — HP & Uttarakhand focus; Great Himalayan NP, Govind Pashu Vihar
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+snow+leopard'
                '+tiger+sanctuary+site:hillpost.in'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Hill Post',
    },

    # ── Gujarat (Gir / Asiatic lion / Wild Ass / Whale Shark / Marine NP) ────
    # No Gujarat daily has a usable direct wildlife RSS feed.
    # This GN search pulls from ALL sources including TOI city sections (Rajkot,
    # Ahmedabad), Gujarat Samachar, Divya Bhaskar, DNA, etc. without site: restriction.
    # Covers the full Gujarat wildlife portfolio beyond just lion/Gir.
    {
        'url': ('https://news.google.com/rss/search?q='
                'gujarat+lion+OR+gujarat+%22wild+ass%22+OR+gujarat+%22whale+shark%22'
                '+OR+gujarat+flamingo+OR+gujarat+blackbuck+OR+gujarat+gir'
                '+OR+gujarat+velavadar+OR+gujarat+dugong+OR+gujarat+bustard'
                '+OR+gujarat+%22marine+national+park%22+OR+gujarat+%22nal+sarovar%22'
                '+OR+gujarat+%22rann+of+kutch%22+OR+gujarat+%22little+rann%22'
                '+OR+gujarat+pangolin+OR+gujarat+%22olive+ridley%22'
                '+OR+gujarat+%22great+indian+bustard%22+OR+gujarat+wolf'
                '+OR+gujarat+%22spiny-tailed+lizard%22+OR+gujarat+%22indian+roller%22'
                '+OR+gujarat+%22lesser+florican%22+OR+gujarat+%22painted+stork%22'
                '+OR+gujarat+%22forest+department%22+OR+gujarat+poaching'
                '+OR+gujarat+%22wildlife+sanctuary%22+OR+gujarat+%22barda+hills%22'
                '+OR+gujarat+%22shoolpaneshwar%22+OR+gujarat+%22jessore%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # ── National ───────────────────────────────────────────────────────────────
    # Hindustan Times — strong UP, Uttarakhand, Gujarat, national coverage
    'https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml',

    # ── Via Google News proxy (direct RSS blocked by Cloudflare / 403) ────────
    # Google pre-filters by wildlife keywords AND serves through Google's CDN,
    # bypassing the source site's bot protection entirely.
    # entry.source.title in each result gives the real publication name.
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:thewire.in'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'The Wire',
    },
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:tribuneindia.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Tribune India',
    },
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:telegraphindia.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Telegraph India',
    },
    {
        'url': ('https://news.google.com/rss/search?q=wildlife+forest+tiger'
                '+elephant+poaching+sanctuary+site:deccanherald.com'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
        'source': 'Deccan Herald',
    },

    # ── State-specific comprehensive queries ──────────────────────────────────
    # Each state query covers its distinctive taxa, PAs, and conservation issues.
    # No site: restriction — pulls from ALL sources (state dailies, city editions,
    # national outlets covering that state). Duplicates are eliminated by URL dedup.
    # No forced_source — real publication name extracted from each GN entry.

    # Maharashtra — leopard HWC near Mumbai/Pune, Tadoba, Melghat, Sahyadri
    {
        'url': ('https://news.google.com/rss/search?q='
                'maharashtra+leopard+OR+maharashtra+tiger+OR+maharashtra+gaur'
                '+OR+maharashtra+%22indian+giant+squirrel%22+OR+maharashtra+wolf'
                '+OR+maharashtra+%22sloth+bear%22+OR+maharashtra+gharial'
                '+OR+maharashtra+tadoba+OR+maharashtra+melghat'
                '+OR+maharashtra+nagzira+OR+maharashtra+sahyadri'
                '+OR+maharashtra+radhanagari+OR+maharashtra+koyna'
                '+OR+maharashtra+%22bor+tiger%22+OR+maharashtra+chandoli'
                '+OR+maharashtra+%22great+indian+bustard%22+OR+maharashtra+pangolin'
                '+OR+maharashtra+%22wildlife+rescue%22+OR+maharashtra+poaching'
                '+OR+maharashtra+%22man-animal+conflict%22+OR+maharashtra+%22forest+fire%22'
                '+OR+maharashtra+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Madhya Pradesh — tiger capital, Ken-Betwa, barasingha, gharial (Chambal)
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22madhya+pradesh%22+tiger+OR+%22madhya+pradesh%22+leopard'
                '+OR+%22madhya+pradesh%22+barasingha+OR+%22madhya+pradesh%22+gharial'
                '+OR+%22madhya+pradesh%22+wolf+OR+%22madhya+pradesh%22+%22sloth+bear%22'
                '+OR+%22madhya+pradesh%22+gaur+OR+%22madhya+pradesh%22+vulture'
                '+OR+kanha+OR+bandhavgarh+OR+panna+OR+satpura'
                '+OR+%22ken-betwa%22+OR+%22ken+betwa%22+OR+nauradehi'
                '+OR+%22sanjay+tiger%22+OR+ratapani+OR+%22chambal+sanctuary%22'
                '+OR+%22madhya+pradesh%22+poaching+OR+%22madhya+pradesh%22+%22forest+fire%22'
                '+OR+%22madhya+pradesh%22+%22tiger+death%22+OR+%22madhya+pradesh%22+corridor'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Rajasthan — GIB, Ranthambhore, desert species, power-line collisions
    {
        'url': ('https://news.google.com/rss/search?q='
                'rajasthan+tiger+OR+rajasthan+%22great+indian+bustard%22'
                '+OR+rajasthan+%22desert+cat%22+OR+rajasthan+caracal'
                '+OR+rajasthan+wolf+OR+rajasthan+chinkara+OR+rajasthan+urial'
                '+OR+rajasthan+leopard+OR+rajasthan+%22indian+gazelle%22'
                '+OR+ranthambore+OR+sariska+OR+%22keoladeo%22+OR+bharatpur+wetland'
                '+OR+%22desert+national+park%22+OR+%22mount+abu%22+wildlife'
                '+OR+%22kumbhalgarh%22+wildlife+OR+%22sita+mata%22+wildlife'
                '+OR+rajasthan+%22power+line%22+bird+OR+rajasthan+bustard+collision'
                '+OR+rajasthan+poaching+OR+rajasthan+%22wildlife+rescue%22'
                '+OR+rajasthan+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Uttarakhand — Corbett, Rajaji, snow leopard, elephant corridors
    {
        'url': ('https://news.google.com/rss/search?q='
                'uttarakhand+tiger+OR+uttarakhand+elephant+OR+uttarakhand+leopard'
                '+OR+uttarakhand+%22snow+leopard%22+OR+uttarakhand+%22red+panda%22'
                '+OR+uttarakhand+%22himalayan+black+bear%22+OR+uttarakhand+%22musk+deer%22'
                '+OR+uttarakhand+goral+OR+uttarakhand+tahr'
                '+OR+uttarakhand+gharial+OR+uttarakhand+mahseer'
                '+OR+%22jim+corbett%22+OR+rajaji+OR+%22nanda+devi%22'
                '+OR+%22valley+of+flowers%22+OR+gangotri+wildlife'
                '+OR+%22kedarnath+wildlife%22+OR+%22govind+pashu+vihar%22'
                '+OR+uttarakhand+%22elephant+corridor%22+OR+uttarakhand+poaching'
                '+OR+uttarakhand+%22man-animal%22+OR+uttarakhand+%22forest+fire%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Odisha — olive ridley mass nesting, Simlipal, Chilika, Bhitarkanika saltwater croc
    {
        'url': ('https://news.google.com/rss/search?q='
                'odisha+elephant+OR+odisha+tiger+OR+odisha+%22olive+ridley%22'
                '+OR+odisha+%22saltwater+crocodile%22+OR+odisha+%22mugger%22'
                '+OR+odisha+%22irrawaddy+dolphin%22+OR+odisha+flamingo'
                '+OR+odisha+%22fishing+cat%22+OR+odisha+pangolin'
                '+OR+simlipal+OR+bhitarkanika+OR+chilika'
                '+OR+gahirmatha+OR+%22debrigarh%22+OR+satkosia'
                '+OR+%22turtle+nesting%22+odisha+OR+%22mass+nesting%22'
                '+OR+odisha+%22wildlife+rescue%22+OR+odisha+poaching'
                '+OR+odisha+%22forest+fire%22+OR+odisha+%22man-animal%22'
                '+OR+odisha+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # West Bengal — Sundarbans, rhino (Gorumara/Jaldapara), North Bengal elephants
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22west+bengal%22+tiger+OR+%22west+bengal%22+rhinoceros'
                '+OR+%22west+bengal%22+elephant+OR+%22west+bengal%22+%22fishing+cat%22'
                '+OR+%22west+bengal%22+%22clouded+leopard%22+OR+%22west+bengal%22+%22gangetic+dolphin%22'
                '+OR+sundarbans+OR+gorumara+OR+jaldapara+OR+%22buxa+tiger%22'
                '+OR+%22neora+valley%22+OR+singalila+OR+chapramari'
                '+OR+%22west+bengal%22+%22mangrove%22+wildlife'
                '+OR+%22west+bengal%22+poaching+OR+%22west+bengal%22+%22wildlife+rescue%22'
                '+OR+%22west+bengal%22+%22forest+fire%22+OR+%22north+bengal%22+wildlife'
                '+OR+%22west+bengal%22+%22man-animal%22+OR+%22west+bengal%22+%22human+wildlife%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Karnataka — Western Ghats, Nagarhole, Bandipur, elephant HWC in Kodagu
    {
        'url': ('https://news.google.com/rss/search?q='
                'karnataka+tiger+OR+karnataka+elephant+OR+karnataka+leopard'
                '+OR+karnataka+%22lion-tailed+macaque%22+OR+karnataka+dhole'
                '+OR+karnataka+gaur+OR+karnataka+%22sloth+bear%22'
                '+OR+karnataka+%22indian+star+tortoise%22+OR+karnataka+%22malabar+hornbill%22'
                '+OR+karnataka+%22king+cobra%22+OR+karnataka+%22giant+squirrel%22'
                '+OR+nagarhole+OR+nagarahole+OR+bandipur+OR+%22brt+tiger%22'
                '+OR+%22kali+tiger%22+OR+dandeli+OR+kudremukh+OR+bhadra+wildlife'
                '+OR+%22ranibennur%22+OR+%22arabithittu%22+OR+%22sharavathi%22+wildlife'
                '+OR+karnataka+poaching+OR+karnataka+%22man-animal%22'
                '+OR+karnataka+%22forest+fire%22+OR+karnataka+%22wildlife+rescue%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Kerala — Periyar, tahr, lion-tailed macaque, Silent Valley, elephant train deaths
    {
        'url': ('https://news.google.com/rss/search?q='
                'kerala+tiger+OR+kerala+elephant+OR+kerala+%22nilgiri+tahr%22'
                '+OR+kerala+%22lion-tailed+macaque%22+OR+kerala+%22great+hornbill%22'
                '+OR+kerala+%22king+cobra%22+OR+kerala+gaur+OR+kerala+leopard'
                '+OR+kerala+%22smooth+otter%22+OR+kerala+%22fishing+cat%22'
                '+OR+kerala+%22malabar+giant+squirrel%22'
                '+OR+periyar+OR+%22silent+valley%22+OR+wayanad+wildlife'
                '+OR+eravikulam+OR+%22parambikulam%22+OR+%22chinnar%22+wildlife'
                '+OR+kerala+%22train+hit%22+elephant+OR+kerala+%22train+accident%22+elephant'
                '+OR+kerala+poaching+OR+kerala+%22man-animal%22+OR+kerala+%22forest+fire%22'
                '+OR+kerala+%22wildlife+rescue%22+OR+kerala+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Tamil Nadu — Mudumalai, Anamalai, tahr, Gulf of Mannar, Point Calimere
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22tamil+nadu%22+tiger+OR+%22tamil+nadu%22+elephant'
                '+OR+%22tamil+nadu%22+%22nilgiri+tahr%22+OR+%22tamil+nadu%22+%22lion-tailed+macaque%22'
                '+OR+%22tamil+nadu%22+gaur+OR+%22tamil+nadu%22+%22sloth+bear%22'
                '+OR+%22tamil+nadu%22+%22olive+ridley%22+OR+%22tamil+nadu%22+dugong'
                '+OR+%22tamil+nadu%22+%22sea+horse%22+OR+%22tamil+nadu%22+%22sea+turtle%22'
                '+OR+mudumalai+OR+%22anamalai%22+OR+%22indira+gandhi+wildlife%22'
                '+OR+%22mukurthi%22+OR+%22point+calimere%22+OR+vedanthangal'
                '+OR+%22gulf+of+mannar%22+OR+%22kalakad+mundanthurai%22'
                '+OR+%22meghamalai%22+OR+%22grizzled+squirrel%22'
                '+OR+%22tamil+nadu%22+poaching+OR+%22tamil+nadu%22+%22man-animal%22'
                '+OR+%22tamil+nadu%22+%22wildlife+rescue%22+OR+%22tamil+nadu%22+%22forest+fire%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Andhra Pradesh / Telangana — Nagarjunasagar, wolf, blackbuck, Rollapadu
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22andhra+pradesh%22+tiger+OR+%22andhra+pradesh%22+%22indian+wolf%22'
                '+OR+%22andhra+pradesh%22+blackbuck+OR+%22andhra+pradesh%22+%22sloth+bear%22'
                '+OR+%22andhra+pradesh%22+%22great+indian+bustard%22+OR+%22andhra+pradesh%22+elephant'
                '+OR+telangana+tiger+OR+telangana+wolf+OR+telangana+%22sloth+bear%22'
                '+OR+telangana+blackbuck+OR+telangana+%22kawal+tiger%22'
                '+OR+%22nagarjunasagar%22+OR+amrabad+OR+%22papikonda%22'
                '+OR+%22rollapadu%22+OR+%22nelapattu%22+OR+%22sri+lankamalleswara%22'
                '+OR+%22andhra+pradesh%22+poaching+OR+telangana+poaching'
                '+OR+%22andhra+pradesh%22+%22wildlife+rescue%22+OR+telangana+%22wildlife+rescue%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Himachal Pradesh — snow leopard (Spiti), western tragopan, Great Himalayan NP
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22himachal+pradesh%22+%22snow+leopard%22+OR+%22himachal+pradesh%22+%22himalayan+bear%22'
                '+OR+%22himachal+pradesh%22+%22musk+deer%22+OR+%22himachal+pradesh%22+bharal'
                '+OR+%22himachal+pradesh%22+%22blue+sheep%22+OR+%22himachal+pradesh%22+%22himalayan+wolf%22'
                '+OR+%22himachal+pradesh%22+%22western+tragopan%22+OR+%22himachal+pradesh%22+%22cheer+pheasant%22'
                '+OR+%22himachal+pradesh%22+%22himalayan+tahr%22+OR+%22himachal+pradesh%22+%22ibex%22'
                '+OR+%22great+himalayan+national+park%22+OR+%22pin+valley%22'
                '+OR+kibber+wildlife+OR+kugti+wildlife+OR+%22lippa+asrang%22'
                '+OR+%22himachal+pradesh%22+poaching+OR+%22himachal+pradesh%22+%22wildlife+rescue%22'
                '+OR+spiti+wildlife+OR+lahaul+wildlife+OR+%22himachal%22+%22camera+trap%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Arunachal Pradesh — hornbill, clouded leopard, Namdapha, Eaglenest
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22arunachal+pradesh%22+hornbill+OR+%22arunachal+pradesh%22+%22clouded+leopard%22'
                '+OR+%22arunachal+pradesh%22+tiger+OR+%22arunachal+pradesh%22+elephant'
                '+OR+%22arunachal+pradesh%22+%22hoolock+gibbon%22+OR+%22arunachal+pradesh%22+%22red+panda%22'
                '+OR+%22arunachal+pradesh%22+takin+OR+%22arunachal+pradesh%22+%22mishmi+takin%22'
                '+OR+%22arunachal+pradesh%22+%22white-bellied+heron%22'
                '+OR+%22arunachal+pradesh%22+%22snow+leopard%22'
                '+OR+namdapha+OR+pakke+wildlife+OR+eaglenest+OR+kamlang+OR+dibang+wildlife'
                '+OR+%22arunachal+pradesh%22+poaching+OR+%22arunachal+pradesh%22+%22wildlife+rescue%22'
                '+OR+%22arunachal+pradesh%22+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Northeast (Meghalaya / Nagaland / Manipur / Mizoram / Tripura / Sikkim)
    # Assam has dedicated sources; this covers the remaining NE states
    {
        'url': ('https://news.google.com/rss/search?q='
                'meghalaya+wildlife+OR+nagaland+wildlife+OR+manipur+wildlife'
                '+OR+mizoram+wildlife+OR+tripura+wildlife+OR+sikkim+wildlife'
                '+OR+meghalaya+%22amur+falcon%22+OR+nagaland+%22amur+falcon%22'
                '+OR+nagaland+hornbill+OR+%22hornbill+festival%22+wildlife'
                '+OR+manipur+%22brow-antlered+deer%22+OR+%22sangai%22'
                '+OR+%22keibul+lamjao%22+OR+%22loktak+lake%22+wildlife'
                '+OR+sikkim+%22red+panda%22+OR+sikkim+%22snow+leopard%22'
                '+OR+%22khangchendzonga%22+OR+meghalaya+%22clouded+leopard%22'
                '+OR+%22dampa%22+wildlife+OR+%22phawngpui%22+OR+%22murlen%22'
                '+OR+%22fakim%22+OR+%22intanki%22+OR+%22sirohi%22'
                '+OR+tripura+%22clouded+leopard%22+OR+tripura+elephant'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Jharkhand / Bihar / Chhattisgarh — wild buffalo, Valmiki, Gangetic dolphin
    {
        'url': ('https://news.google.com/rss/search?q='
                'jharkhand+elephant+OR+jharkhand+tiger+OR+jharkhand+%22forest+fire%22'
                '+OR+jharkhand+poaching+OR+%22palamau%22+OR+%22betla+national+park%22'
                '+OR+bihar+%22gangetic+dolphin%22+OR+%22valmiki+tiger%22+OR+%22vikramshila%22'
                '+OR+bihar+%22gharial%22+OR+bihar+%22wildlife+rescue%22+OR+bihar+elephant'
                '+OR+chhattisgarh+%22wild+buffalo%22+OR+chhattisgarh+elephant'
                '+OR+chhattisgarh+tiger+OR+chhattisgarh+wolf+OR+chhattisgarh+gaur'
                '+OR+indravati+OR+achanakmar+OR+%22udanti+sitanadi%22+OR+%22barnawapara%22'
                '+OR+chhattisgarh+poaching+OR+chhattisgarh+%22forest+fire%22'
                '+OR+chhattisgarh+%22wildlife+rescue%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Jammu & Kashmir / Ladakh — hangul, snow leopard, black-necked crane, Changthang
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22jammu+and+kashmir%22+%22snow+leopard%22+OR+ladakh+%22snow+leopard%22'
                '+OR+%22jammu+and+kashmir%22+hangul+OR+%22kashmir+stag%22'
                '+OR+ladakh+%22black-necked+crane%22+OR+ladakh+%22bar-headed+goose%22'
                '+OR+ladakh+%22tibetan+wolf%22+OR+ladakh+%22pallas+cat%22'
                '+OR+ladakh+%22marco+polo+sheep%22+OR+ladakh+urial+OR+ladakh+bharal'
                '+OR+%22jammu+and+kashmir%22+leopard+OR+%22jammu+and+kashmir%22+%22musk+deer%22'
                '+OR+dachigam+OR+%22hemis+national+park%22+OR+%22salim+ali%22+wildlife'
                '+OR+%22changthang%22+wildlife+OR+%22trikuta%22+wildlife'
                '+OR+ladakh+%22wildlife+rescue%22+OR+ladakh+poaching'
                '+OR+%22jammu+and+kashmir%22+poaching+OR+%22jammu+and+kashmir%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Punjab / Haryana / Delhi NCR — bird migration, blackbuck, ramsar wetlands
    {
        'url': ('https://news.google.com/rss/search?q='
                'punjab+%22migratory+bird%22+OR+punjab+blackbuck+OR+punjab+%22wildlife+rescue%22'
                '+OR+haryana+blackbuck+OR+haryana+%22migratory+bird%22+OR+haryana+%22wildlife+rescue%22'
                '+OR+%22sultan+pur%22+bird+OR+%22sultanpur+national+park%22'
                '+OR+%22kalagarh+bird%22+OR+%22harike%22+wetland+OR+%22ropar+wetland%22'
                '+OR+%22bhadohi%22+wetland+OR+%22pong+dam%22+bird'
                '+OR+delhi+%22migratory+bird%22+OR+delhi+%22wildlife+rescue%22'
                '+OR+delhi+%22okhla+bird%22+OR+%22yamuna+biodiversity%22'
                '+OR+%22aravalli+wildlife%22+OR+haryana+wolf+OR+haryana+%22nilgai%22'
                '+OR+punjab+poaching+OR+haryana+poaching'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # Goa — marine turtles, mangroves, Bhagwan Mahavir, Mhadei, mollem
    {
        'url': ('https://news.google.com/rss/search?q='
                'goa+%22olive+ridley%22+OR+goa+%22sea+turtle%22+OR+goa+%22turtle+nesting%22'
                '+OR+goa+leopard+OR+goa+gaur+OR+goa+%22giant+squirrel%22'
                '+OR+goa+%22king+cobra%22+OR+goa+mangrove+OR+goa+%22wildlife+rescue%22'
                '+OR+%22bhagwan+mahavir%22+OR+%22mollem%22+wildlife+OR+%22mhadei%22+wildlife'
                '+OR+%22cotigao%22+OR+%22bondla%22+wildlife+OR+goa+poaching'
                '+OR+goa+%22forest+fire%22+OR+goa+%22forest+department%22+wildlife'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # ── Broad catch-all queries (no site: restriction) ────────────────────────
    # These act as a permanent safety net for city-level articles, new publications,
    # and any source not in the list above. GN aggregates ALL Indian sources.
    # Duplicates from specific feeds above are eliminated by URL deduplication.
    # No forced_source — real publication name extracted from each GN entry.

    # 1. Big mammals, predators, ungulates
    {
        'url': ('https://news.google.com/rss/search?q='
                'tiger+OR+leopard+OR+elephant+OR+rhinoceros+OR+rhino'
                '+OR+%22snow+leopard%22+OR+%22clouded+leopard%22'
                '+OR+%22sloth+bear%22+OR+%22sun+bear%22+OR+%22asiatic+lion%22'
                '+OR+dhole+OR+wolf+OR+pangolin+OR+%22red+panda%22'
                '+OR+%22wild+dog%22+OR+%22striped+hyena%22+OR+nilgai'
                '+OR+gaur+OR+bison+OR+%22four-horned+antelope%22'
                '+OR+%22blackbuck%22+OR+chinkara+OR+%22indian+gazelle%22'
                '+OR+hangul+OR+%22kashmir+stag%22+OR+%22musk+deer%22'
                '+OR+%22barasingha%22+OR+%22swamp+deer%22+OR+chausingha'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # 2. Birds (threatened, migratory, flagship)
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22great+indian+bustard%22+OR+%22lesser+florican%22'
                '+OR+hornbill+OR+%22sarus+crane%22+OR+flamingo'
                '+OR+vulture+OR+%22forest+owlet%22+OR+%22jerdon%27s+courser%22'
                '+OR+pelican+OR+%22painted+stork%22+OR+%22black-necked+crane%22'
                '+OR+%22demoiselle+crane%22+OR+%22migratory+bird%22'
                '+OR+avifauna+OR+osprey+OR+%22indian+skimmer%22'
                '+OR+%22spoon-billed+sandpiper%22+OR+%22sociable+lapwing%22'
                '+OR+%22siberian+crane%22+OR+%22bar-headed+goose%22'
                '+OR+%22steppe+eagle%22+OR+%22eastern+imperial+eagle%22'
                '+OR+%22pallas%27s+fish+eagle%22+OR+%22white-rumped+vulture%22'
                '+OR+%22red-headed+vulture%22+OR+%22egyptian+vulture%22'
                '+OR+%22long-billed+vulture%22+OR+%22indian+vulture%22'
                '+OR+%22florican%22+OR+%22bird+species%22+OR+%22bird+count%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # 3. Marine, freshwater, herpetofauna
    {
        'url': ('https://news.google.com/rss/search?q='
                '%22whale+shark%22+OR+%22river+dolphin%22+OR+%22gangetic+dolphin%22'
                '+OR+gharial+OR+%22olive+ridley%22+OR+%22sea+turtle%22'
                '+OR+%22leatherback+turtle%22+OR+%22hawksbill+turtle%22'
                '+OR+%22green+turtle%22+OR+dugong+OR+%22coral+reef%22'
                '+OR+mangrove+OR+mahseer+OR+%22mugger+crocodile%22'
                '+OR+%22saltwater+crocodile%22+OR+python+OR+%22king+cobra%22'
                '+OR+%22indian+rock+python%22+OR+%22monitor+lizard%22'
                '+OR+%22marine+turtle%22+OR+%22nest+site%22+OR+%22turtle+nesting%22'
                '+OR+%22humpback+whale%22+OR+%22blue+whale%22+OR+%22sperm+whale%22'
                '+OR+%22irrawaddy+dolphin%22+OR+%22hilsa%22+OR+%22freshwater%22+fish'
                '+OR+%22fishing+cat%22+OR+%22smooth+otter%22+OR+otter+river'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # 4. Conservation, threats, conflict, policy
    {
        'url': ('https://news.google.com/rss/search?q='
                'poaching+OR+%22wildlife+trafficking%22'
                '+OR+%22human+wildlife+conflict%22+OR+%22man-animal+conflict%22'
                '+OR+%22elephant+corridor%22+OR+%22tiger+corridor%22'
                '+OR+%22wildlife+corridor%22+OR+%22forest+fire%22+OR+wildfire'
                '+OR+%22habitat+loss%22+OR+%22forest+encroachment%22'
                '+OR+%22wildlife+rescue%22+OR+%22forest+department%22+wildlife'
                '+OR+%22wildlife+crime%22+OR+%22wildlife+trafficking%22'
                '+OR+%22compensatory+afforestation%22+OR+%22forest+clearance%22'
                '+OR+%22project+tiger%22+OR+%22project+elephant%22'
                '+OR+%22wii+report%22+OR+%22census+wildlife%22'
                '+OR+%22captive+elephant%22+OR+%22captive+animal%22'
                '+OR+%22rewilding%22+OR+%22translocation%22+wildlife'
                '+OR+%22radio+collar%22+OR+%22camera+trap%22'
                '+OR+%22wildlife+underpass%22+OR+%22eco+bridge%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },

    # 5. Protected area names — catches PA-specific news even without species terms
    {
        'url': ('https://news.google.com/rss/search?q='
                'kaziranga+OR+sundarbans+OR+%22jim+corbett%22'
                '+OR+bandipur+OR+ranthambore+OR+%22gir+forest%22'
                '+OR+kanha+OR+pench+OR+tadoba+OR+nagarhole+OR+nagarahole'
                '+OR+simlipal+OR+manas+OR+namdapha+OR+periyar'
                '+OR+sariska+OR+bharatpur+OR+chilika+OR+bhitarkanika'
                '+OR+%22valley+of+flowers%22+OR+%22great+himalayan+national+park%22'
                '+OR+%22silent+valley%22+OR+%22anamalai%22+OR+%22mudumalai%22'
                '+OR+%22bandhavgarh%22+OR+%22panna+tiger%22+OR+%22satpura%22'
                '+OR+%22dudhwa%22+OR+%22katerniaghat%22+OR+%22rajaji%22'
                '+OR+%22kibber%22+OR+%22pin+valley%22+OR+%22great+indian+bustard+sanctuary%22'
                '+OR+%22pakke%22+OR+%22eaglenest%22+OR+%22dibang%22+OR+%22kamlang%22'
                '+OR+%22nagzira%22+OR+%22melghat%22+OR+%22sahyadri%22+OR+%22radhanagari%22'
                '+OR+%22bhadra%22+OR+%22kudremukh%22+OR+%22pushpagiri%22'
                '+OR+%22indravati%22+OR+%22achanakmar%22+OR+%22udanti%22'
                '+OR+%22dampa%22+OR+%22phawngpui%22+OR+%22murlen%22'
                '+OR+%22intanki%22+OR+%22fakim%22+OR+%22khangchendzonga%22'
                '&hl=en-IN&gl=IN&ceid=IN:en'),
    },
]

# ── Comprehensive species + ecology keywords ────────────────────────────────
KEYWORDS = [

    # ── MAMMALS ──────────────────────────────────────────────────────────────
    # Big cats & felids
    'tiger', 'leopard', 'cheetah', 'snow leopard', 'clouded leopard',
    'fishing cat', 'rusty-spotted cat', 'jungle cat', 'leopard cat', 'caracal',
    # Elephants & rhinos
    'elephant', 'rhinoceros', 'rhino', 'one-horned rhino',
    # Bears
    'sloth bear', 'himalayan bear', 'black bear', 'brown bear', 'sun bear',
    # Canids & hyena
    'wolf', 'dhole', 'indian wild dog', 'wild dog', 'jackal', 'fox', 'hyena',
    # Primates
    'langur', 'macaque', 'gibbon', 'hoolock gibbon', 'lion-tailed macaque',
    'bonnet macaque', 'slow loris', 'monkey',
    # Deer & antelope
    'deer', 'sambar', 'chital', 'spotted deer', 'barasingha', 'swamp deer',
    'hog deer', 'barking deer', 'mouse deer', 'musk deer',
    'nilgai', 'blackbuck', 'chinkara', 'four-horned antelope', 'gazelle',
    # Mountain ungulates
    'nilgiri tahr', 'markhor', 'ibex', 'blue sheep', 'bharal', 'hangul',
    'kashmir stag', 'mithun', 'gaur', 'bison', 'wild buffalo',
    # Lions
    'lion', 'asiatic lion', 'gir lion',
    # Pangolin, panda & others
    'pangolin', 'red panda', 'giant squirrel', 'malabar squirrel',
    'flying squirrel', 'porcupine', 'Indian crested porcupine',
    # Otters, civets & mustelids
    'otter', 'smooth-coated otter', 'small-clawed otter',
    'civet', 'palm civet', 'binturong', 'mongoose',
    # Wild pig
    'wild boar',
    # Bats
    'bat', 'flying fox', 'fruit bat',
    # Marine mammals
    'dolphin', 'river dolphin', 'gangetic dolphin', 'irrawaddy dolphin',
    'whale', 'blue whale', 'humpback whale', 'sperm whale', 'porpoise', 'dugong',

    # ── BIRDS ────────────────────────────────────────────────────────────────
    # Raptors
    'eagle', 'vulture', 'osprey', 'falcon', 'kite', 'hawk', 'harrier',
    'buzzard', 'kestrel', 'raptor', 'shikra', 'goshawk',
    # Bustards & cranes
    'bustard', 'great indian bustard', 'sarus crane', 'demoiselle crane', 'crane',
    # Large waterbirds
    'flamingo', 'pelican', 'stork', 'spoonbill', 'ibis', 'adjutant',
    'painted stork', 'cormorant', 'darter', 'egret', 'heron',
    # Hornbills, kingfishers & related
    'hornbill', 'kingfisher', 'bee-eater', 'roller', 'hoopoe', 'barbet',
    # Owls & nightjars
    'owl', 'owlet', 'nightjar', 'frogmouth',
    # Parakeets & pigeons
    'parakeet', 'parrot', 'pigeon', 'dove',
    # Peacock
    'peacock', 'peafowl',
    # Pheasants & junglefowl
    'pheasant', 'junglefowl', 'jungle fowl', 'partridge', 'quail',
    # Passerines & others
    'sunbird', 'woodpecker', 'drongo', 'pitta', 'bulbul', 'babbler',
    'warbler', 'flycatcher', 'robin', 'thrush', 'myna', 'starling',
    'weaver', 'munia', 'sparrow',
    # Shorebirds & wetland birds
    'plover', 'sandpiper', 'lapwing', 'tern', 'skimmer', 'snipe',
    'avocet', 'stilt', 'pratincole',
    # General bird terms
    'avian', 'avifauna', 'migratory bird', 'bird species', 'bird migration',
    'nesting bird', 'breeding bird', 'waterbird', 'wader', 'seabird',

    # ── REPTILES ─────────────────────────────────────────────────────────────
    'crocodile', 'gharial', 'mugger',
    'python', 'king cobra', 'cobra', 'krait', 'viper', 'russell viper',
    'rat snake', 'sand boa', 'boa', 'sea snake',
    'monitor lizard', 'lizard', 'gecko', 'skink', 'chameleon', 'agama',
    'turtle', 'tortoise', 'sea turtle', 'olive ridley', 'leatherback', 'hawksbill',
    'green turtle', 'loggerhead', 'softshell turtle',

    # ── AMPHIBIANS ───────────────────────────────────────────────────────────
    'frog', 'toad', 'salamander', 'newt', 'caecilian', 'amphibian',
    'tree frog', 'night frog', 'shrub frog', 'torrent frog',

    # ── FISH ─────────────────────────────────────────────────────────────────
    'mahseer', 'hilsa', 'rohu', 'catfish', 'snakehead',
    'shark', 'whale shark', 'ray', 'manta ray', 'sawfish',
    'seahorse', 'pufferfish', 'clownfish', 'coral fish',
    'eel', 'river fish', 'freshwater fish', 'marine fish',

    # ── INVERTEBRATES ────────────────────────────────────────────────────────
    'butterfly', 'butterflies', 'moth', 'dragonfly', 'dragonflies', 'damselfly', 'odonate',
    'beetle', 'wasp', 'bee', 'honeybee', 'bumblebee',
    'ant', 'termite', 'firefly', 'glowworm', 'cicada',
    'spider', 'scorpion', 'crab', 'horseshoe crab',
    'coral', 'coral reef', 'jellyfish', 'sea urchin',
    'octopus', 'squid', 'cuttlefish', 'mollusc',
    'snail', 'earthworm',

    # ── PLANTS & FUNGI ───────────────────────────────────────────────────────
    'orchid', 'pitcher plant', 'sundew', 'cycad', 'tree fern',
    'rhododendron', 'magnolia', 'wild banana', 'bamboo species',
    'medicinal plant', 'plant species', 'endemic plant', 'invasive plant',
    'algae', 'seagrass', 'moss', 'lichen', 'fungi', 'mushroom species',
    'foraminifera', 'diatom', 'plankton', 'microorganism', 'zooplankton',

    # ── ECOLOGY & CONSERVATION ───────────────────────────────────────────────
    'wildlife', 'poaching', 'poacher', 'poached', 'wildlife trafficking', 'wildlife crime',
    'national park', 'wildlife sanctuary', 'tiger reserve', 'biosphere reserve',
    'wildlife corridor', 'elephant corridor', 'forest corridor',
    'wildlife conservation', 'species conservation', 'biodiversity conservation',
    'forest', 'forest department', 'forest fire', 'forest cover', 'forest loss',
    'reserve forest', 'protected forest', 'protected area',
    'deforestation', 'afforestation', 'reforestation',
    'habitat loss', 'habitat destruction', 'habitat fragmentation',
    'human-wildlife conflict', 'man-animal conflict',
    'eco-sensitive', 'biodiversity', 'mangrove', 'wetland',
    'endangered species', 'threatened species', 'extinct species',
    'invasive species', 'endemic species', 'new species', 'new to science',
    'species discovered', 'species found', 'species recorded',
    'camera trap', 'wildlife survey', 'wildlife census', 'wildlife monitoring',
    'WII', 'WWF', 'WTI', 'IUCN', 'wildlife institute',
    'ecosystem', 'ecology', 'ecological', 'carbon sequestration',
    'marine ecosystem', 'coastal ecosystem', 'freshwater ecosystem',
    'forest ecosystem', 'wildlife ecosystem', 'river ecosystem',
    'woodland', 'native forest', 'tree cover',
    'migratory', 'nesting', 'breeding', 'spawning',
    'animal behaviour', 'conservation biology',
    'citizen science', 'species',

    # ── PROTECTED AREAS ──────────────────────────────────────────────────────
    'kaziranga', 'sundarbans', 'corbett', 'bandipur', 'ranthambore',
    'bandhavgarh', 'kanha', 'tadoba', 'nagarhole', 'periyar',
    'satpura', 'melghat', 'pench', 'simlipal', 'manas',
    'gir forest', 'sariska', 'rajaji', 'dudhwa', 'mudumalai',
    'anamalai', 'kalakad', 'mundanthurai', 'agasthyamalai',
    'wayanad', 'parambikulam', 'silent valley', 'mukurthi',
    'pakke', 'eaglenest', 'dibru-saikhowa', 'nameri',
    'buxa', 'gorumara', 'jaldapara', 'chapramari',
    'orang', 'pobitora', 'laokhowa',
    'bhadra', 'kudremukh', 'pushpagiri', 'brahmagiri',
    'indravati', 'panna', 'achanakmar', 'udanti',
    'nokrek', 'dampa', 'khangchendzonga', 'singalila',
    # J&K / Ladakh
    'dachigam', 'hemis', 'kishtwar', 'salim ali', 'jasrota', 'surinsar', 'mansar',
    # Himachal Pradesh / Uttarakhand
    'great himalayan', 'pin valley', 'kibber', 'kugti', 'simbalbara',
    'nandhaur', 'govind pashu vihar', 'askot', 'sonanadi',
    # Uttar Pradesh
    'pilibhit', 'sohagi barwa', 'hastinapur', 'nawabganj', 'katarniaghat',
    # Bihar / Jharkhand
    'valmiki', 'betla', 'palamau',
    # Andhra Pradesh / Telangana
    'nagarjunasagar', 'papikonda', 'kawal', 'coringa', 'eturnagaram',
    'kinnersani', 'kolleru', 'pocharam', 'manjira',
    # Karnataka
    'biligiri', 'brt tiger', 'dandeli', 'kali tiger', 'ranibennur',
    # Odisha
    'simlipal', 'bhitarkanika', 'chilika', 'satkosia', 'debrigarh',
    'hadgarh', 'nandankanan',
    # West Bengal
    'buxa', 'gorumara', 'jaldapara', 'chapramari', 'neora valley', 'senchal',
    # Maharashtra
    'nawegaon', 'umred', 'radhanagari', 'bhimashankar', 'koyna', 'phansad',
    # Tamil Nadu
    'grizzled squirrel', 'guindy', 'pulicat', 'vedanthangal',
    'point calimere', 'megamalai', 'topslip', 'srivilliputhur',
    # Gujarat
    'gir', 'wild ass', 'velavadar', 'nal sarovar', 'jessore', 'vansda', 'shoolpaneshwar',
    'rann of kutch',
]

# ── Exclusion list — any match blocks the article ────────────────────────────
# Catches politics, infrastructure, crime, sports, finance etc. that
# incidentally mention an ecology keyword.
EXCLUDE_KEYWORDS = [
    # Military / security
    'militant', 'militants', 'terrorist', 'terrorists', 'encounter', 'ceasefire',
    'army operation', 'security forces', 'paramilitary', 'naxal', 'maoist', 'insurgent',
    'drone strike', 'airstrike', 'gunfight', 'firing', 'crpf', 'bsf',
    'bunker', 'hideout', 'hideouts', 'smuggler', 'smugglers',
    'lone-wolf', 'lone wolf',  # terror attack terminology — not the animal
    # Awards / prizes that share animal/ecology words
    'wolf prize',  # physics/mathematics prize — not the animal
    'operation tiger',  # political codename used by Maharashtra BJP — not the animal
    # Politics / government
    'election', 'constituency', 'mla', 'mp ', ' mp,', 'cabinet approves',
    'union cabinet', 'lok sabha', 'rajya sabha', 'parliament',
    'rebellion', 'political', 'party', 'tmc', 'bjp', 'congress', 'aap',
    'nda ', ' upa', 'chief minister', 'governor appoints',
    'anti-encroachment drive', 'demolition drive',
    'legislators', 'lawmaker', 'offsite', 'review huddle', 'party huddle',
    # Infrastructure / civic
    'metro', 'railway', 'highway', 'flyover', 'road widening',
    'airport link', 'commonwealth games', 'expressway',
    'mosque demolished', 'temple demolished', 'mazar',
    # Crime / law & order
    'murder', 'rape', 'kidnap', 'robbery', 'fraud', 'scam', 'arrest',
    'blast', 'bomb', 'explosion', 'riot', 'curfew', 'internet blackout',
    'prohibitory orders',
    # Sports
    'ipl', 'cricket', 'football', 'hockey match', 'tennis', 'wrestling',
    'commonwealth games',
    # Finance / economy
    'stock market', 'sensex', 'nifty', 'budget', 'gdp', 'inflation',
    'interest rate', 'rbi ', 'sebi ', 'ipo ',
    # Tech / startup (catches "deep-tech ecosystem", "healthcare sector", etc.)
    'deep-tech', 'deep tech', 'startup ecosystem', 'tech ecosystem',
    'fintech', 'edtech', 'healthtech', 'healthcare sector',
    'artificial intelligence', 'machine learning', 'data centre',
]

NEWS_JSON = os.path.join(os.path.dirname(__file__), '..', 'docs', 'news.json')
INDIA_CENTER = (20.5937, 78.9629)  # generic pin — reject these

# Sources whose content is not wildlife news (exam prep, lifestyle, etc.)
BLOCKED_SOURCES = {
    'Vajiram & Ravi',
    'Luxury Lifestyle Magazine',
}


def _normalize_url(url: str) -> str:
    """Strip query string and fragment for deduplication.
    Same article with ?utm_source, ?ref, etc. attached is treated as identical."""
    try:
        p = urlparse(url)
        return urlunparse(p._replace(query='', fragment=''))
    except Exception:
        return url


def load_existing():
    try:
        with open(NEWS_JSON, encoding='utf-8') as f:
            raw = f.read()
    except FileNotFoundError:
        logger.info("news.json not found — starting fresh")
        return []

    # Detect git merge-conflict markers left in the file
    if '<<<<<<< ' in raw or '=======' in raw or '>>>>>>> ' in raw:
        raise RuntimeError(
            "news.json contains git merge-conflict markers. "
            "Resolve the conflict manually before running the pipeline."
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"news.json is corrupted (JSONDecodeError: {e}). "
            "Restore from git before running the pipeline."
        ) from e

    if not isinstance(data, list):
        raise RuntimeError("news.json root element is not a list — file is malformed.")

    return data


import re as _re

def fix_encoding(text: str) -> str:
    """Fix cp1252/utf-8 mojibake (e.g. 'Ã¢â‚¬Ëœ' → curly quote).
    Some feeds double/triple encode; apply up to 3 passes until stable.
    Only accepts the fixed version if it contains no replacement chars (U+FFFD)
    and is actually different — avoids corrupting already-correct text."""
    if not text:
        return text
    for _ in range(3):
        try:
            fixed = text.encode('cp1252').decode('utf-8')
            if fixed == text:
                break
            # Reject if fix introduced replacement characters
            if '�' in fixed:
                break
            text = fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
    return text

def _word_in(phrase: str, text: str) -> bool:
    """True if phrase appears as whole word(s) in text (case-insensitive).
    Handles common English plurals (tiger→tigers, leopard→leopards, forest→forests).
    """
    escaped = _re.escape(phrase.lower())
    return bool(_re.search(r'\b' + escaped + r'(?:s|es)?\b', text))

def matches_keywords(title: str, description: str = '') -> bool:
    """
    Two-stage check:
    1. Exclusion — whole-word match against title+description.
    2. Inclusion — at least one KEYWORD must appear as whole word(s) in the TITLE.
       Word-boundary matching prevents 'owl' matching inside 'Gachibowli', etc.
    """
    combined = (title + ' ' + description).lower()
    title_lower = title.lower()

    # Stage 1: exclude
    if any(_word_in(ex, combined) for ex in EXCLUDE_KEYWORDS):
        return False

    # Stage 2: keyword must appear in the TITLE as whole word/phrase
    return any(_word_in(kw, title_lower) for kw in KEYWORDS)


def parse_date(entry) -> str:
    for attr in ('published', 'updated'):
        val = getattr(entry, attr, None)
        if val:
            try:
                dt = dateparser.parse(val)
                if dt:
                    return dt.strftime('%Y-%m-%d')
            except Exception:
                pass
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0 '
    'wildlife-news-map/1.0 (+https://github.com/nikunjfriends25-droid/wildlife-news-map)'
)

def fetch_feed(url: str) -> list:
    try:
        # Pass a browser-like User-Agent — some feeds (e.g. The Wire) block
        # feedparser's default "python-feedparser/..." agent.
        feed = feedparser.parse(url, agent=USER_AGENT)
        if feed.bozo and not feed.entries:
            logger.warning(f"Feed error ({url}): {feed.bozo_exception}")
            return []
        logger.info(f"  Got {len(feed.entries)} entries")
        return feed.entries
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return []


def source_name(url: str) -> str:
    mapping = {
        'downtoearth.org':    'Down To Earth',
        'thewire.in':         'The Wire',
        'mongabay.com':       'Mongabay India',
        'thehindu.com':       'The Hindu',
        'timesofindia':       'Times of India',
        'ndtv':               'NDTV',
        'indianexpress.com':  'Indian Express',
        'hindustantimes.com': 'Hindustan Times',
        'researchmatters.in': 'Research Matters',
        'nature.com':         'Nature India',
        'assamtribune.com':    'Assam Tribune',
        'nenow.in':            'Northeast Now',
        'eastmojo.com':        'EastMojo',
        'greaterkashmir.com':  'Greater Kashmir',
        'risingkashmir.com':   'Rising Kashmir',
        'gujaratsamachar.com': 'Gujarat Samachar',
        'divyabhaskar.co.in':  'Divya Bhaskar',
        'dnaindia.com':        'DNA India',
    }
    for key, name in mapping.items():
        if key in url:
            return name
    try:
        return url.split('/')[2]
    except IndexError:
        return url


def main():
    existing = load_existing()
    # Normalize stored URLs so articles with tracking params (?utm_source etc.)
    # are not re-fetched as if they were new articles.
    seen_urls = {_normalize_url(a['url']) for a in existing}
    logger.info(f"Loaded {len(existing)} existing articles")

    new_articles = []

    for src in SOURCES:
        # SOURCES entries can be a plain URL string or a dict with url + source override
        if isinstance(src, dict):
            feed_url = src['url']
            forced_source = src.get('source')  # e.g. 'The Wire' for Google News proxies
        else:
            feed_url = src
            forced_source = None

        logger.info(f"Fetching {feed_url[:80]}")
        entries = fetch_feed(feed_url)

        for entry in entries:
            url = getattr(entry, 'link', None)
            if not url:
                continue
            norm_url = _normalize_url(url)
            if norm_url in seen_urls:
                continue

            title = fix_encoding(getattr(entry, 'title', '') or '')
            description = fix_encoding(getattr(entry, 'summary', '') or '')

            # Skip Google News search-result pages that sneak in as entries
            if title.startswith('You searched for'):
                continue

            # For broad GN queries (no forced_source), extract the real publication
            # name from each entry's source field. GN populates entry.source.title
            # with the outlet name (e.g. "Times of India", "Deccan Chronicle").
            gn_source = None
            if not forced_source and 'news.google.com' in feed_url:
                gn_source = getattr(getattr(entry, 'source', None), 'title', None)

            if (forced_source or gn_source) in BLOCKED_SOURCES:
                logger.debug(f"Blocked source skipped: {forced_source or gn_source}")
                continue

            # Strip "- Publication Name" suffix Google News appends to titles
            pub_name = forced_source or gn_source
            if pub_name:
                for sep in (f' - {pub_name}', f' | {pub_name}'):
                    if title.endswith(sep):
                        title = title[:-len(sep)].strip()
                        break

            if not matches_keywords(title, description):
                continue

            pub_date = parse_date(entry)

            place_name, lat, lon = extract_location(title, description)

            if place_name is None:
                logger.debug(f"No location found: {title[:60]}")
                continue

            if lat is None or lon is None:
                coords = geocode(place_name)
                if coords is None:
                    logger.debug(f"Geocoding failed: {place_name}")
                    continue
                lat, lon = coords

            # Skip articles that landed on generic India centre
            if abs(lat - INDIA_CENTER[0]) < 0.01 and abs(lon - INDIA_CENTER[1]) < 0.01:
                logger.debug(f"Skipping India-centre pin: {title[:50]}")
                continue

            if forced_source:
                sname = forced_source
            elif gn_source:
                sname = gn_source
            else:
                sname = source_name(feed_url)

            article = {
                'headline': title.strip(),
                'url': url,
                'source': sname,
                'published': pub_date,
                'place_name': place_name,
                'lat': lat,
                'lon': lon,
            }
            new_articles.append(article)
            seen_urls.add(norm_url)
            logger.info(f"  + {title[:50]} @ {place_name}")

    merged = existing + new_articles
    merged.sort(key=lambda a: a.get('published', ''), reverse=True)

    # Safety check: abort if merged count drops by more than 20% vs existing.
    # This catches silent data loss (corrupted load, race condition, etc.)
    if existing and len(merged) < len(existing) * 0.80:
        raise RuntimeError(
            f"SAFETY ABORT: merged count {len(merged)} is more than 20% below "
            f"existing count {len(existing)}. Something went wrong — not writing."
        )

    os.makedirs(os.path.dirname(NEWS_JSON), exist_ok=True)
    with open(NEWS_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote {len(merged)} articles to docs/news.json ({len(new_articles)} new)")


if __name__ == '__main__':
    main()
