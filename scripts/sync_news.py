#!/usr/bin/env python3
"""Refresh short BBC Sport Football headlines for the static site."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import json
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data' / 'news.json'
FEED = 'https://feeds.bbci.co.uk/sport/football/rss.xml'

try:
    request = urllib.request.Request(FEED, headers={'User-Agent': 'AlexMyrusTalksSports Football/Soccer dashboard'})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())
    stories = []
    for item in root.findall('./channel/item')[:30]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        date = (item.findtext('pubDate') or '').strip()
        if not title or not link:
            continue
        try:
            date = parsedate_to_datetime(date).astimezone(timezone.utc).isoformat()
        except Exception:
            pass
        stories.append({'title': title, 'link': link, 'date': date, 'source': 'BBC Sport Football'})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({'generatedAt': datetime.now(timezone.utc).isoformat(), 'source': FEED, 'stories': stories}, ensure_ascii=False, indent=2) + '\n')
except Exception as error:
    if not OUTPUT.exists():
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps({'generatedAt': datetime.now(timezone.utc).isoformat(), 'source': FEED, 'stories': [], 'error': str(error)}, ensure_ascii=False, indent=2) + '\n')
    print('BBC Sport feed refresh failed; keeping the previous news snapshot:', error)
