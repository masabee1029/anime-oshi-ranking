#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AniList から作品のジャケット画像 URL を取得して covers.json に保存する。
- anilist_id があるもの: id_in で 50 件ずつまとめて取得
- 配信ランキングなど id のないもの: タイトル検索（キャッシュ済みは飛ばす）
"""
import csv, json, os, re, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.expanduser("~/knowledge-os/raw/anime")
ST = os.path.join(DATA, "streaming")
CACHE = os.path.join(HERE, "covers.json")
URL = "https://graphql.anilist.co"
HDR = {"Content-Type": "application/json", "Accept": "application/json",
       "User-Agent": "anime-oshi-ranking/1.0 (github.com/masabee1029/anime-oshi-ranking)"}

cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {"by_id": {}, "by_title": {}}

def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    for attempt in range(6):
        req = urllib.request.Request(URL, data=body, headers=HDR)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if int(r.headers.get("X-RateLimit-Remaining", "10")) < 3:
                    time.sleep(10)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt >= 2: raise SystemExit("AniList の回数制限が続くため打ち切り（次回の実行で続きから取得）")
                time.sleep(min(int(e.headers.get("Retry-After", "60")), 65)); continue
            if e.code == 404:
                return {}
            time.sleep(5)
    return {}

def norm(t):
    return re.sub(r"[\s　:：・!！?？\-－~～「」『』()（）]", "", (t or "")).lower()

# ---- 1. id つき ----
ids = set()
for fn in ("world_top.csv", "japan_top.csv", "seasonal_1970_2026.csv"):
    for r in csv.DictReader(open(os.path.join(DATA, fn), encoding="utf-8")):
        if fn.startswith("seasonal"):
            try:
                if int(r.get("popularity") or 0) < 5000: continue
            except ValueError: continue
        if r.get("anilist_id"): ids.add(int(r["anilist_id"]))
todo = sorted(i for i in ids if str(i) not in cache["by_id"])
print("ids total", len(ids), "to fetch", len(todo))
Q = """query($ids:[Int]){Page(perPage:50){media(id_in:$ids,type:ANIME){id coverImage{large} title{native romaji english}}}}"""
for i in range(0, len(todo), 50):
    chunk = todo[i:i+50]
    d = gql(Q, {"ids": chunk})
    for m in (d.get("data") or {}).get("Page", {}).get("media", []) or []:
        cache["by_id"][str(m["id"])] = m["coverImage"]["large"]
        for t in (m["title"] or {}).values():
            if t: cache["by_title"].setdefault(norm(t), m["coverImage"]["large"])
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(2.2)
    print("  fetched", min(i+50, len(todo)), "/", len(todo))

# ---- 2. タイトルのみ ----
titles = []
def add(*ts):
    for t in ts:
        if t and norm(t) not in cache["by_title"] and t not in titles: titles.append(t)
for fn, cols in (("world_allservices_ranking.csv", ("title_ja", "title")),
                 ("japan_allservices_ranking.csv", ("title", "original_title")),
                 ("world_by_service_ranking.csv", ("title_ja", "title")),
                 ("netflix_anime_ranking_global.csv", ("anime_title_ja", "show_title")),
                 ("netflix_anime_ranking_by_country.csv", ("anime_title_ja", "show_title")),
                 ("filmarks_trend_anime.csv", ("title",))):
    for r in csv.DictReader(open(os.path.join(ST, fn), encoding="utf-8")):
        if fn.startswith("netflix_anime_ranking_by_country") and r.get("country") != "JP": continue
        add(*[r.get(c) for c in cols])
print("titles to search", len(titles))
QS = """query($s:String){Page(perPage:1){media(search:$s,type:ANIME,isAdult:false){id coverImage{large} title{native romaji english}}}}"""
MAX_SEARCH = 120  # 1 回の実行で検索する上限（残りは次回）
for n, t in enumerate(titles[:MAX_SEARCH], 1):
    s = re.sub(r"(第?\d+期|Season \d+|シーズン\d+|第\d+クール|\(\d{4}\)|劇場版|TVアニメ)", " ", t).strip() or t
    d = gql(QS, {"s": s})
    ms = (d.get("data") or {}).get("Page", {}).get("media", []) or []
    if ms:
        url = ms[0]["coverImage"]["large"]
        cache["by_title"][norm(t)] = url
        for tt in (ms[0]["title"] or {}).values():
            if tt: cache["by_title"].setdefault(norm(tt), url)
    else:
        cache["by_title"][norm(t)] = None
    if n % 10 == 0:
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False); print("  searched", n, "/", len(titles))
    time.sleep(2.2)
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
print("done: by_id", len(cache["by_id"]), "by_title", len(cache["by_title"]))
