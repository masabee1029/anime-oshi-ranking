#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABEMA・DMM TV の全作品検索の結果（runner の window.__svout を写した TSV）を services.json に入れる（2026-11-07）。
  python3 svc_apply.py ABEMA 結果.tsv
  python3 svc_apply.py "DMM TV" 結果.tsv
1 行 = 作品キー<TAB>サービスの作品ID<TAB>サービス上の作品名。今回見つからなかった作品は、そのサービスの記録を消す（配信が終わった扱い）。
"""
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "services.json")
svc, path = sys.argv[1], sys.argv[2]
data = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip()]
if len(rows) < 5:
    sys.exit("結果が少なすぎます（%d 行）。読み取りの失敗かもしれないので書き込みません" % len(rows))
today = datetime.date.today().isoformat()
hit = {r[0]: {"id": r[1], "name": r[2] if len(r) > 2 else "", "date": today} for r in rows if len(r) >= 2}
before = sum(1 for v in data.values() if svc in v)
for k in list(data):
    data[k].pop(svc, None)
    if not data[k]: del data[k]
for k, v in hit.items():
    data.setdefault(k, {})[svc] = v
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("%s: %d 作品（前回 %d）" % (svc, len(hit), before))
