#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作品ごとの「日本でどこで観られるか」を JustWatch から取って watch.json にためる。
build.py が書き出す titles_index.json の作品が対象。30 日以内に取ったものは飛ばす。
"""
import json, os, re, subprocess, time, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "titles_index.json")
OUT = os.path.join(HERE, "watch.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TODAY = datetime.date.today()
MAX_PER_RUN = 450
Q = """query($q:String!){popularTitles(country:JP,first:4,filter:{searchQuery:$q}){edges{node{objectType
content(country:JP,language:"ja"){title originalTitle originalReleaseYear}
offers(country:JP,platform:WEB){monetizationType package{clearName}}}}}}"""

def norm(t):
    return re.sub(r"[\s　:：・!！?？\-－~～「」『』()（）]", "", (t or "")).lower()
def strip_extra(t):
    t = re.sub(r"[【\[（(「『].*?[】\]）)」』]", " ", t or "")
    t = re.sub(r"(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*\d+|全\s*\d+\s*章|劇場版)", " ", t)
    return t.strip(" 　")

def series_name(t):
    t = re.sub(r"^(新劇場版|劇場版|映画)\s*", "", t or "")
    t = re.sub(r"[「」【】『』]", "", t)
    m = re.split(r"[ 　’'。.\-－～~（(〈]|第|Season|SEASON|The Final|FINAL|THE FINAL|[ⅡⅢⅣ]|II|\d+(st|nd|rd|th)", t)
    base = (m[0] or "").strip()
    if re.fullmatch(r"[\x00-\x7f]+", base) and len(base) < 4: return None   # THE / 86 など短い英数字は誤一致しやすい
    return base if len(base) >= 2 else None

def pkg_name(n):
    if n.startswith("Netflix"): return "Netflix"
    if n.startswith("Amazon Prime Video"): return "Prime Video"
    if n == "Amazon Video": return "Amazon"
    if "d Anime" in n or "dアニメ" in n: return "dアニメストア"
    if n.endswith("Amazon Channel"): return "Prime Video チャンネル"
    if n == "Disney Plus": return "Disney+"
    if n.startswith("Apple TV"): return "Apple TV"
    if n.startswith("Google Play"): return "Google Play"
    if "U-NEXT" in n or "U-Next" in n: return "U-NEXT"
    return n

def query(q):
    body = json.dumps({"query": Q, "variables": {"q": q}})
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "-m", "30", "-H", "Content-Type: application/json", "-A", UA, "-d", body,
                            "https://apis.justwatch.com/graphql"], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            return d["data"]["popularTitles"]["edges"]
        except Exception:
            time.sleep(5)
    return []

def pick(edges, names, year):
    want = {norm(n) for n in names if n} | {norm(strip_extra(n)) for n in names if n}
    want.discard("")
    best = None
    for e in edges:
        c = e["node"]["content"]
        cand = {norm(c.get("title")), norm(c.get("originalTitle"))}
        y = c.get("originalReleaseYear")
        exact = bool(cand & want)
        yok = (not year) or (y and abs(int(y) - int(year)) <= 1)
        if exact and yok: return e["node"]
        if exact and best is None: best = e["node"]
    if best: return best
    # 完全一致が無ければ、年が合う先頭の結果を部分一致で採用
    for e in edges[:1]:
        c = e["node"]["content"]; y = c.get("originalReleaseYear")
        t = norm(c.get("title"))
        if year and y and abs(int(y) - int(year)) <= 1 and any(w and (w in t or t in w) for w in want):
            return e["node"]
    return None

idx = json.load(open(IDX, encoding="utf-8"))
cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
todo = []
for it in idx:
    c = cache.get(it["key"])
    if c and (TODAY - datetime.date.fromisoformat(c["date"])).days < 30 and (c.get("jw_title") or c.get("series_tried")): continue
    todo.append(it)
print("titles", len(idx), "to fetch", len(todo[:MAX_PER_RUN]))
for n, it in enumerate(todo[:MAX_PER_RUN], 1):
    names = [it["title"]] + it.get("alts", [])
    node = None
    for q in dict.fromkeys([strip_extra(it["title"]) or it["title"]] + [a for a in it.get("alts", []) if a][:1]):
        node = pick(query(q), names, it.get("year"))
        time.sleep(0.4)
        if node: break
    series = None
    if not node:
        # 続編・劇場版はシリーズ名で探し直す（JustWatch はシーズンを 1 作品にまとめているため）
        base = series_name(it["title"])
        if base and norm(base) != norm(it["title"]):
            node = pick(query(base), [base], None)
            time.sleep(0.4)
            if node: series = base
    rec = {"date": TODAY.isoformat(), "flatrate": [], "free": [], "rent_buy": [], "series_tried": True}
    if series: rec["series"] = series
    if node:
        rec["jw_title"] = node["content"]["title"]; rec["jw_year"] = node["content"].get("originalReleaseYear")
        for o in node.get("offers") or []:
            nm = pkg_name(o["package"]["clearName"]); mt = o["monetizationType"]
            slot = "flatrate" if mt == "FLATRATE" else ("free" if mt in ("FREE", "ADS") else ("rent_buy" if mt in ("RENT", "BUY") else None))
            if slot and nm not in rec[slot]: rec[slot].append(nm)
        # 見放題にあるものは無料・レンタル側から外す
        rec["free"] = [x for x in rec["free"] if x not in rec["flatrate"]]
        rec["rent_buy"] = [x for x in rec["rent_buy"] if x not in rec["flatrate"]]
    cache[it["key"]] = rec
    if n % 20 == 0:
        json.dump(cache, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("  ", n)
json.dump(cache, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
found = sum(1 for v in cache.values() if v.get("jw_title"))
print("done", len(cache), "matched", found)
