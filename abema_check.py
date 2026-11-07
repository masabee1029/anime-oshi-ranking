#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「ABEMAで観る」ボタンを出している作品が、いまも ABEMA で観られるかを毎月確かめる（2026-11-07 ユーザー「毎月一回確認をタスクに記録、実行」）。
  python3 abema_check.py list            確かめる ABEMA の作品ページ（URL と作品名）を JSON で出す
  python3 abema_check.py apply 結果.json  ブラウザで数えた結果 {url: エピソード数} を abema_check.json に書く
エピソードが 0 本のページ（配信終了）の作品は、build.py が ABEMA ボタンを出さなくなる。
"""
import csv, json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.expanduser("~/knowledge-os/raw/anime")
OUT = os.path.join(HERE, "abema_check.json")

def targets():
    t = {}
    vf = os.path.join(DATA, "my_viewing", "watched_titles.csv")
    for r in csv.DictReader(open(vf, encoding="utf-8")) if os.path.exists(vf) else []:
        if r.get("service") == "ABEMA" and r.get("url"):
            t.setdefault(r["url"], set()).update(x for x in (r.get("title"), r.get("title_native")) if x)
    cfg = json.load(open(os.path.join(HERE, "affiliate.json"), encoding="utf-8"))
    for name, url in (cfg.get("abema_urls") or {}).items():   # 手で足した作品 {作品名: ABEMA の作品ページ}
        t.setdefault(url, set()).add(name)
    return {u: sorted(n) for u, n in t.items()}

if sys.argv[1:2] == ["list"]:
    print(json.dumps(targets(), ensure_ascii=False))
elif sys.argv[1:2] == ["apply"]:
    res = json.load(open(sys.argv[2], encoding="utf-8"))
    tg = targets()
    items = [{"url": u, "names": tg.get(u, []), "episodes": n, "ok": n > 0} for u, n in res.items()]
    json.dump({"checked": datetime.date.today().isoformat(), "items": items}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ng = [i for i in items if not i["ok"]]
    print("checked", len(items), "ok", len(items) - len(ng), "ended", len(ng))
    for i in ng: print("  配信なし:", " / ".join(i["names"]), i["url"])
else:
    print(__doc__)
