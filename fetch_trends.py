#!/usr/bin/env python3
"""今季・前季アニメの「人気（AniList の popularity＝リストに入れた人の数）」の日ごとの記録を AniList から取って trends.json に足す。
build.py はこれを使って、季節ページに「毎月の順位の動き」グラフを描く。
- 対象: 今季と前季（seasonal_1970_2026.csv の各 50 作品）
- 前回までに取った日付に届いたら、それより古いページは取らない（毎月の更新では新しい日の分だけ取る）
- AniList の回数制限（429）が出たら、言われた秒数だけ待ってやり直す
"""
import csv, datetime, json, os, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SEASONAL = os.path.expanduser("~/knowledge-os/raw/anime/seasonal_1970_2026.csv")
OUT = os.path.join(HERE, "trends.json")
URL = "https://graphql.anilist.co"
UA = "knowledge-os-anime-fetch/1.0 (curl-compatible)"
Q = "query($id:Int,$p:Int){Media(id:$id){trends(sort:DATE_DESC,page:$p,perPage:25){pageInfo{hasNextPage} nodes{date popularity}}}}"
COUR = {1: "冬", 4: "春", 7: "夏", 10: "秋"}

def cour_of(d):
    m = (d.month - 1) // 3 * 3 + 1
    return d.year, COUR[m], datetime.date(d.year, m, 1)

def prev_cour(y, start):
    s = (start - datetime.timedelta(days=1)).replace(day=1)
    s = s.replace(month=(s.month - 1) // 3 * 3 + 1)
    return s.year, COUR[s.month], s

def post(var):
    body = json.dumps({"query": Q, "variables": var}).encode()
    for _ in range(6):
        req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if int(r.headers.get("X-RateLimit-Remaining", "10")) < 3: time.sleep(20)
                return json.load(r)["data"]["Media"]["trends"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "60")) + 1); continue
            if e.code == 404: return None
            raise
    raise RuntimeError("AniList が応答しません")

def main():
    today = datetime.date.today()
    cy, cc, cstart = cour_of(today)
    py, pc, pstart = prev_cour(cy, cstart)
    rows = list(csv.DictReader(open(SEASONAL, encoding="utf-8")))
    want = [(r, start) for r in rows for (y, c, start) in ((cy, cc, cstart), (py, pc, pstart))
            if r["year"] == str(y) and r["cour"] == c and r.get("anilist_id")]
    data = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    for i, (r, start) in enumerate(want, 1):
        aid = r["anilist_id"]; have = data.setdefault(aid, {})
        stop = (start - datetime.timedelta(days=7)).isoformat()
        p, new = 1, 0
        while True:
            t = post({"id": int(aid), "p": p})
            if not t: break
            reached = False
            for n in t["nodes"]:
                d = datetime.date.fromtimestamp(n["date"]).isoformat()
                if d in have and d < today.isoformat(): reached = True
                if n.get("popularity") is not None:
                    if d not in have: new += 1
                    have[d] = n["popularity"]
                if d < stop: reached = True
            if reached or not t["pageInfo"]["hasNextPage"]: break
            p += 1; time.sleep(0.7)
        print("%d/%d %s %s +%d日" % (i, len(want), aid, r["title_native"][:20], new), flush=True)
        time.sleep(0.7)
        if i % 10 == 0:
            json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("saved", OUT, len(data), "作品")

if __name__ == "__main__":
    main()
