#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作品ごとの「公式 YouTube の PV」を探して pv.json にためる。
YouTube Data API v3 のキーを .secrets.json の youtube_api_key に入れて使う（git には入れない）。
公式チャンネルの動画だけを採用し、ファンの切り抜きや無断転載は使わない。
1 回の実行で最大 90 作品（API の 1 日の無料枠 10,000 のうち検索 1 回 = 100 を使うため）。
"""
import json, os, re, subprocess, urllib.parse, datetime, time

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = os.path.join(HERE, ".secrets.json")
IDX = os.path.join(HERE, "titles_index.json")
OUT = os.path.join(HERE, "pv.json")
MAX_PER_RUN = int(os.environ.get("PV_MAX", "90"))
TODAY = datetime.date.today().isoformat()

# 公式とみなすチャンネル（アニメの製作・配給・配信の公式）。ここに無くても「公式」「official」を含めば候補にする
OFFICIAL = ["アニプレックス", "Aniplex", "TOHO animation", "東宝", "KADOKAWA", "角川", "ポニーキャニオン", "PONY CANYON",
            "avex", "エイベックス", "バンダイナムコ", "BANDAI NAMCO", "サンライズ", "東映アニメーション", "Toei Animation",
            "キングレコード", "KING RECORDS", "フライングドッグ", "ワーナー", "Warner", "NBCユニバーサル", "MAPPA",
            "ufotable", "京都アニメーション", "Netflix Japan", "Netflix Anime", "Crunchyroll", "Disney", "ディズニー",
            "集英社", "講談社", "小学館", "スクウェア・エニックス", "SQUARE ENIX", "アニメイト", "DMM pictures", "Pierrot",
            "ぴえろ", "TMS", "トムス", "日本アニメーション", "スタジオジブリ", "STUDIO GHIBLI", "コミックス・ウェーブ", "CoMix Wave",
            "Production I.G", "WIT STUDIO", "CloverWorks", "A-1 Pictures", "トライガー", "TRIGGER", "テレビ東京", "TBS", "日テレ",
            "フジテレビ", "ABEMA", "dアニメストア", "U-NEXT", "Prime Video", "アミューズ", "ムービック", "GENCO"]
PV_WORDS = ["PV", "予告", "トレーラー", "Trailer", "trailer", "ティザー", "Teaser", "CM", "特報"]
BAD_WORDS = ["切り抜き", "反応", "考察", "解説", "MAD", "AMV", "reaction", "Reaction", "まとめ", "歌ってみた", "弾いてみた",
             "実写", "ハリウッド", "MOBILE", "ドッカンバトル", "ゲーム", "アプリ", "発売告知", "発売記念", "巻発売", "文庫",
             "Blu-ray", "DVD", "グッズ", "コラボ"]
# アニメの PV だと分かる言葉（実写映画・小説・ゲームの PV を避けるため、どれか 1 つを必須にする）
ANIME_WORDS = ["アニメ", "TV", "Anime", "ANIME", "劇場版", "放送", "ON AIR", "Season", "SEASON", "期", "クール"]

def norm(t):
    return re.sub(r"[\s　:：・!！?？\-－~～「」『』()（）【】〈〉]", "", (t or "")).lower()

def api(path, params, key):
    params = dict(params, key=key)
    url = "https://www.googleapis.com/youtube/v3/%s?%s" % (path, urllib.parse.urlencode(params))
    r = subprocess.run(["curl", "-s", "-m", "30", url], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")

def is_official(ch):
    c = ch or ""
    return any(o.lower() in c.lower() for o in OFFICIAL) or "公式" in c or "official" in c.lower()

def choose(items, title):
    t = norm(re.sub(r"^(新劇場版|劇場版|映画)\s*", "", title))
    core = t[:max(4, min(len(t), 8))]          # 題名の頭 8 文字で一致を見る
    for it in items:
        sn = it["snippet"]; vt = sn["title"]; ch = sn["channelTitle"]
        if any(b in vt for b in BAD_WORDS): continue
        if not any(w in vt for w in PV_WORDS): continue
        if not any(w in vt for w in ANIME_WORDS): continue
        if core not in norm(vt): continue
        if not is_official(ch): continue
        return {"video_id": it["id"]["videoId"], "video_title": vt, "channel": ch,
                "published": sn.get("publishedAt", "")[:10], "date": TODAY}
    return None

if not os.path.exists(SECRETS):
    raise SystemExit("youtube_api_key が未設定（.secrets.json）")
key = json.load(open(SECRETS, encoding="utf-8")).get("youtube_api_key")
if not key: raise SystemExit("youtube_api_key が空")
idx = json.load(open(IDX, encoding="utf-8"))
cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
# 新しい基準に合わなくなった採用済みの動画は、探し直す対象に戻す
for k, v in list(cache.items()):
    if v.get("video_id"):
        vt = v.get("video_title", "")
        if any(b in vt for b in BAD_WORDS) or not any(w in vt for w in ANIME_WORDS):
            del cache[k]
todo = [it for it in idx if it["key"] not in cache][:MAX_PER_RUN]
print("titles", len(idx), "done", len(cache), "this run", len(todo))
for n, it in enumerate(todo, 1):
    q = "%s 公式 PV" % re.sub(r"[【】]", " ", it["title"])
    d = api("search", {"part": "snippet", "type": "video", "maxResults": 10, "q": q,
                       "regionCode": "JP", "relevanceLanguage": "ja", "videoEmbeddable": "true"}, key)
    if "error" in d:
        print("API error:", d["error"].get("message")); break
    cache[it["key"]] = choose(d.get("items", []), it["title"]) or {"none": True, "date": TODAY}
    if n % 10 == 0:
        json.dump(cache, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("  ", n)
    time.sleep(0.2)
json.dump(cache, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", len(cache), "found", sum(1 for v in cache.values() if v.get("video_id")))
