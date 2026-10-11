#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推しアニメランキング サイト生成スクリプト
~/knowledge-os/raw/anime のデータから docs/ 以下の HTML を生成する。
使い方: python3 build.py
"""
import csv, json, os, html, urllib.parse, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.expanduser("~/knowledge-os/raw/anime")
ST = os.path.join(DATA, "streaming")
OUT = os.path.join(HERE, "docs")
CFG = json.load(open(os.path.join(HERE, "affiliate.json"), encoding="utf-8"))
TODAY = datetime.date.today().isoformat()

GENRE_JA = {
    "Action": "アクション", "Adventure": "冒険", "Comedy": "コメディ", "Drama": "ドラマ",
    "Fantasy": "ファンタジー", "Romance": "恋愛", "Sci-Fi": "SF", "Slice of Life": "日常",
    "Sports": "スポーツ", "Supernatural": "超常", "Mystery": "ミステリー", "Psychological": "心理",
    "Thriller": "スリラー", "Horror": "ホラー", "Mecha": "ロボット", "Music": "音楽",
    "Mahou Shoujo": "魔法少女", "Ecchi": None, "Hentai": None,
}

def esc(s):
    return html.escape(str(s if s is not None else ""))

def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ---------- アフィリエイトリンク ----------
def amazon_link(title):
    q = urllib.parse.quote_plus(title + " Blu-ray")
    url = "https://www.amazon.co.jp/s?k=" + q
    if CFG.get("amazon_tag"):
        url += "&tag=" + CFG["amazon_tag"]
    return url

def rakuten_link(title):
    search = "https://search.rakuten.co.jp/search/mall/" + urllib.parse.quote(title) + "/"
    if CFG.get("rakuten_affiliate_id"):
        return ("https://hb.afl.rakuten.co.jp/hgc/" + CFG["rakuten_affiliate_id"] +
                "/?pc=" + urllib.parse.quote(search, safe=""))
    return search

def shop_buttons(title):
    btns = ['<a class="btn amz" href="%s" target="_blank" rel="nofollow sponsored noopener">Amazon</a>' % esc(amazon_link(title)),
            '<a class="btn rkt" href="%s" target="_blank" rel="nofollow sponsored noopener">楽天</a>' % esc(rakuten_link(title))]
    if CFG.get("moshimo_unext_url"):
        btns.append('<a class="btn unx" href="%s" target="_blank" rel="nofollow sponsored noopener">U-NEXTで観る</a>' % esc(CFG["moshimo_unext_url"]))
    if CFG.get("moshimo_dmmtv_url"):
        btns.append('<a class="btn dmm" href="%s" target="_blank" rel="nofollow sponsored noopener">DMM TVで観る</a>' % esc(CFG["moshimo_dmmtv_url"]))
    return '<div class="shop">%s</div>' % "".join(btns)

# ---------- ページ枠 ----------
NAV = [("index.html", "トップ"), ("now-japan.html", "国内いま人気"), ("now-world.html", "世界いま人気"),
       ("best-world.html", "歴代・世界評価"), ("netflix.html", "Netflix"), ("genre.html", "ジャンル別"),
       ("decade.html", "年代別")]

def page(title, body, desc="", path_depth=0):
    rel = "../" * path_depth
    nav = "".join('<a href="%s%s">%s</a>' % (rel, h, t) for h, t in NAV)
    site = CFG["site_name"]
    contact = CFG.get("contact_url") or (rel + "about.html")
    return """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s | %s</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="%sstyle.css">
</head><body>
<header><a class="logo" href="%sindex.html">%s</a><nav>%s</nav></header>
<p class="pr">本サイトはアフィリエイト広告（Amazonアソシエイト・楽天アフィリエイト等）を利用しています。</p>
<main>%s</main>
<footer>
<p>データ: AniList / Netflix Tudum 公式Top10 / JustWatch / Filmarks をもとに集計。最終更新 %s</p>
<p><a href="%sabout.html">このサイトについて</a> ・ <a href="%sprivacy.html">プライバシーポリシー</a> ・ <a href="%s">お問い合わせ</a></p>
<p>&copy; %s</p>
</footer></body></html>""" % (esc(title), esc(site), esc(desc or title), rel, rel, esc(site), nav, body, TODAY,
                              rel, rel, esc(contact), esc(site))

def write(name, content):
    p = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

def rank_list(items, show_shop=True):
    """items: list of dict(rank,title,sub,meta)"""
    rows = []
    for it in items:
        rows.append('<li><span class="rk">%s</span><div class="body"><div class="tt">%s</div>'
                    '<div class="sub">%s</div>%s%s</div></li>' % (
                        esc(it["rank"]), esc(it["title"]), esc(it.get("sub", "")),
                        ('<div class="meta">%s</div>' % esc(it["meta"])) if it.get("meta") else "",
                        shop_buttons(it["title"]) if show_shop else ""))
    return '<ol class="rank">%s</ol>' % "".join(rows)

def jp_title(r):
    return r.get("title_native") or r.get("title_romaji") or r.get("title_english") or ""

def genres_ja(g):
    out = []
    for x in (g or "").split("|"):
        j = GENRE_JA.get(x, x)
        if j: out.append(j)
    return "・".join(out)

# ---------- データ読み込み ----------
world = [r for r in read_json(os.path.join(DATA, "world_top.json")) if r.get("ranking") == "world_score"]
seasonal = read_csv(os.path.join(DATA, "seasonal_1970_2026.csv"))
now_w = read_csv(os.path.join(ST, "world_allservices_ranking.csv"))
now_j = read_csv(os.path.join(ST, "japan_allservices_ranking.csv"))
nf_g = read_csv(os.path.join(ST, "netflix_anime_ranking_global.csv"))
nf_c = [r for r in read_csv(os.path.join(ST, "netflix_anime_ranking_by_country.csv")) if r["country"] == "JP"]
flm = read_csv(os.path.join(ST, "filmarks_trend_anime.csv"))
svc = read_csv(os.path.join(ST, "world_by_service_ranking.csv"))
snap = now_w[0]["snapshot_date"] if now_w else TODAY

def is_adult(r):
    return "Hentai" in (r.get("genres") or "")
world = [r for r in world if not is_adult(r)]

# ---------- 国内いま人気 ----------
def now_items(rows, n=30):
    out = []
    for r in rows[:n]:
        t = r.get("title_ja") or r.get("title")
        if r.get("original_title") and r.get("title"):
            t = r["title"]
        sub = []
        if r.get("countries_in_top30"): sub.append("%s か国でTOP30入り" % r["countries_in_top30"])
        if r.get("top1_countries") and r["top1_countries"] != "0": sub.append("%s か国で1位" % r["top1_countries"])
        if r.get("year"): sub.append("%s年" % r["year"])
        if r.get("netflix_views"):
            try: sub.append("Netflix累計 %s万回再生" % format(int(float(r["netflix_views"])) // 10000, ","))
            except ValueError: pass
        out.append({"rank": r["rank"], "title": t, "sub": " / ".join(sub)})
    return out

body = """<h1>国内いま人気のアニメ TOP30（全配信サービス合算）</h1>
<p class="lead">Netflix・Prime Video・U-NEXT・dアニメストア・Disney+・Hulu などの国内ランキングを合算した、いま日本で観られているアニメです（集計日 %s、毎月更新）。</p>
%s
<h2>Filmarks で話題のアニメ</h2>
<p class="lead">レビューサイト Filmarks の「話題のアニメ」。数字は5点満点の平均評価。</p>
%s""" % (esc(snap), rank_list(now_items(now_j)),
         rank_list([{"rank": r["rank"], "title": r["title"], "sub": "評価 %s / 5.0" % r["score_5"]} for r in flm[:20]]))
write("now-japan.html", page("国内いま人気のアニメ TOP30", body, "日本の配信サービス全体で今月人気のアニメランキング"))

body = """<h1>世界いま人気のアニメ TOP30（27か国・全配信合算）</h1>
<p class="lead">世界27か国の Netflix・Prime Video・Disney+・Crunchyroll・Hulu・HBO Max・Apple TV+ のランキングを合算（集計日 %s）。</p>
%s""" % (esc(snap), rank_list(now_items(now_w)))
write("now-world.html", page("世界いま人気のアニメ TOP30", body, "世界27か国の配信ランキングを合算した今月のアニメ人気TOP30"))

# ---------- 歴代・世界評価 ----------
def anilist_items(rows, n=100):
    out = []
    for i, r in enumerate(rows[:n], 1):
        sub = "評価 %s点 / %s / %s年 %s" % (r.get("average_score") or r.get("mean_score"), r.get("format"),
                                         r.get("season_year"), r.get("studio") or "")
        out.append({"rank": r.get("rank") or i, "title": jp_title(r), "sub": sub, "meta": genres_ja(r.get("genres"))})
    return out

body = """<h1>歴代アニメ 世界評価ランキング TOP100</h1>
<p class="lead">世界最大級のアニメデータベース AniList の平均スコア順。海外ファンからの評価の高さを示します。</p>
%s""" % rank_list(anilist_items(world))
write("best-world.html", page("歴代アニメ 世界評価ランキング TOP100", body, "AniList 平均スコアによる歴代アニメ世界評価TOP100"))

# ---------- Netflix ----------
def nf_items(rows, n=30, views=True):
    out = []
    for r in rows[:n]:
        sub = ["TOP10入り %s週" % r["weeks"], "最高 %s位" % r["best"]]
        if views and r.get("views"):
            sub.append("累計 %s万回再生" % format(int(float(r["views"])) // 10000, ","))
        out.append({"rank": r["rank"], "title": r.get("anime_title_ja") or r["show_title"], "sub": " / ".join(sub)})
    return out

body = """<h1>Netflix アニメランキング</h1>
<h2>世界 TOP30（公式週間TOP10の累計）</h2>
<p class="lead">Netflix 公式「Tudum Top 10」の世界集計。再生回数は Netflix が公表している唯一の公式数字です。</p>
%s
<h2>日本 TOP30</h2>
<p class="lead">日本の Netflix 週間TOP10に入った週数の多い順。</p>
%s""" % (rank_list(nf_items(nf_g)), rank_list(nf_items(nf_c, views=False)))
write("netflix.html", page("Netflix アニメランキング 世界・日本", body, "Netflix公式Top10に基づくアニメの世界・日本ランキング"))

# ---------- サービス別（トップに要約） ----------
by_svc = collections.OrderedDict()
for r in svc:
    by_svc.setdefault(r["service"], []).append(r)

# ---------- ジャンル別 ----------
genre_map = collections.defaultdict(list)
for r in world:
    for g in (r.get("genres") or "").split("|"):
        if g and GENRE_JA.get(g, g):
            genre_map[g].append(r)
links = []
for g, rows in sorted(genre_map.items(), key=lambda kv: -len(kv[1])):
    if len(rows) < 10: continue
    name = GENRE_JA.get(g, g)
    fn = "genre/%s.html" % g.lower().replace(" ", "-")
    links.append('<li><a href="%s">%s（%d作品）</a></li>' % (fn, esc(name), len(rows)))
    b = "<h1>%s アニメ おすすめランキング TOP30</h1><p class=\"lead\">世界評価（AniList スコア）順の%sジャンル TOP30。</p>%s" % (
        esc(name), esc(name), rank_list([dict(it, rank=i) for i, it in enumerate(anilist_items(rows, 30), 1)]))
    write(fn, page("%s アニメ おすすめランキング" % name, b, "%sジャンルのおすすめアニメTOP30" % name, 1))
write("genre.html", page("ジャンル別おすすめアニメ", "<h1>ジャンル別おすすめアニメ</h1><ul class=\"links\">%s</ul>" % "".join(links)))

# ---------- 年代別 ----------
dec = collections.defaultdict(dict)
for r in seasonal:
    if is_adult(r) or not r.get("average_score"): continue
    try:
        y = int(r["year"]); sc = int(r["average_score"]); pop = int(r["popularity"] or 0)
    except ValueError: continue
    if pop < 5000: continue
    d = (y // 10) * 10
    key = r["anilist_id"]
    if key not in dec[d]:
        dec[d][key] = r
links = []
for d in sorted(dec):
    rows = sorted(dec[d].values(), key=lambda r: (-int(r["average_score"]), -int(r["popularity"] or 0)))[:30]
    if len(rows) < 5: continue
    fn = "decade/%ds.html" % d
    links.append('<li><a href="%s">%d年代のおすすめアニメ</a></li>' % (fn, d))
    b = "<h1>%d年代 おすすめアニメ TOP%d</h1><p class=\"lead\">%d年代に放送・公開された作品を世界評価順に。</p>%s" % (
        d, len(rows), d, rank_list([dict(it, rank=i) for i, it in enumerate(anilist_items(rows, 30), 1)]))
    write(fn, page("%d年代 おすすめアニメ" % d, b, "%d年代の名作アニメランキング" % d, 1))
write("decade.html", page("年代別おすすめアニメ", "<h1>年代別おすすめアニメ</h1><ul class=\"links\">%s</ul>" % "".join(links)))

# ---------- トップ ----------
def mini(items, href, title):
    lis = "".join('<li><span class="rk">%s</span>%s</li>' % (esc(i["rank"]), esc(i["title"])) for i in items[:5])
    return '<section class="card"><h2><a href="%s">%s</a></h2><ol>%s</ol><a class="more" href="%s">続きを見る →</a></section>' % (href, esc(title), lis, href)

svc_cards = ""
for s, rows in by_svc.items():
    svc_cards += '<div class="svc"><h3>%s</h3><ol>%s</ol></div>' % (
        esc(s), "".join('<li>%s</li>' % esc(r.get("title_ja") or r["title"]) for r in rows[:3]))

body = """<section class="hero"><h1>%s</h1>
<p>世界27か国・国内12サービスの配信ランキングと、歴代の評価データから「いま観るべきアニメ」を毎月更新で紹介します。</p></section>
<div class="grid">%s%s%s%s</div>
<h2>配信サービス別 世界TOP3</h2><div class="svcgrid">%s</div>
<h2>探す</h2><p><a href="genre.html">ジャンル別</a> ・ <a href="decade.html">年代別</a></p>
""" % (esc(CFG["site_name"]),
       mini(now_items(now_j), "now-japan.html", "国内いま人気"),
       mini(now_items(now_w), "now-world.html", "世界いま人気"),
       mini(nf_items(nf_g), "netflix.html", "Netflix 世界"),
       mini(anilist_items(world), "best-world.html", "歴代・世界評価"),
       svc_cards)
write("index.html", page("トップ", body, "配信ランキングと歴代評価でえらぶ、いま観るべきおすすめアニメ"))

# ---------- 固定ページ ----------
write("about.html", page("このサイトについて", """<h1>このサイトについて</h1>
<p>「%s」は、世界と日本の配信ランキング・レビューサイトの評価データを毎月集計し、おすすめアニメを紹介する個人運営サイトです。</p>
<h2>データの出典</h2>
<ul><li>AniList（世界最大級のアニメデータベース）: 歴代評価・ジャンル・年代</li>
<li>Netflix Tudum 公式 Top 10: 週間ランキング・再生回数</li>
<li>JustWatch: 各国・各配信サービスの人気ランキング</li>
<li>Filmarks: 話題のアニメ・5段階評価</li></ul>
<h2>運営者</h2><p>Masabee（YouTube: <a href="https://www.youtube.com/@Masabee1029" target="_blank" rel="noopener">@Masabee1029</a>）</p>
<h2>お問い合わせ</h2><p>%s</p>
<h2>広告について</h2><p>当サイトは Amazon.co.jp アソシエイト、楽天アフィリエイト、もしもアフィリエイト等のアフィリエイトプログラムに参加しています。リンク先での購入・契約により当サイトに紹介料が支払われることがありますが、ランキングの順位は収益によって変わりません。</p>
""" % (esc(CFG["site_name"]), ('<a href="%s">お問い合わせフォーム</a>' % esc(CFG["contact_url"])) if CFG.get("contact_url") else "準備中（YouTube チャンネルのコメント欄からご連絡ください）")))

write("privacy.html", page("プライバシーポリシー", """<h1>プライバシーポリシー</h1>
<h2>広告の配信について</h2>
<p>当サイトは、Amazon.co.jp を宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。また楽天アフィリエイト、もしもアフィリエイトを利用しています。</p>
<h2>アクセス解析について</h2>
<p>当サイトでは、今後 Google アナリティクス等のアクセス解析ツールを利用する場合があります。これらはトラフィックデータ収集のために Cookie を使用しますが、個人を特定するものではありません。</p>
<h2>免責事項</h2>
<p>当サイトの情報は、できる限り正確な情報を掲載するよう努めていますが、ランキングは外部データの集計であり、正確性・最新性を保証するものではありません。リンク先の商品・サービスについては各提供元にお問い合わせください。</p>
<p>制定日: 2026年10月11日</p>"""))

# ---------- CSS ----------
write("style.css", """
:root{--bg:#0f1115;--card:#171a21;--tx:#e8e8ea;--mu:#9aa0ab;--ac:#ff6b9d;--line:#262a33}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.6}
a{color:var(--ac)}header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;padding:12px 16px;border-bottom:1px solid var(--line);background:var(--card)}
.logo{font-weight:700;font-size:1.2rem;text-decoration:none;color:var(--tx)}nav{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.9rem}nav a{text-decoration:none;color:var(--mu)}nav a:hover{color:var(--ac)}
.pr{font-size:.75rem;color:var(--mu);margin:6px 16px}main{max-width:860px;margin:0 auto;padding:8px 16px 40px}
h1{font-size:1.5rem;margin:16px 0 8px}h2{font-size:1.2rem;margin:28px 0 8px;border-left:4px solid var(--ac);padding-left:8px}.lead{color:var(--mu);font-size:.95rem}
ol.rank{list-style:none;padding:0;margin:0}ol.rank li{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}
.rk{flex:0 0 2.2em;font-size:1.4rem;font-weight:800;color:var(--ac);text-align:right}ol.rank li:nth-child(-n+3) .rk{color:#ffd166}
.body{flex:1;min-width:0}.tt{font-weight:700;font-size:1.05rem}.sub,.meta{font-size:.82rem;color:var(--mu)}
.shop{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.btn{font-size:.78rem;padding:4px 10px;border-radius:999px;text-decoration:none;color:#fff;background:#444}
.btn.amz{background:#e47911}.btn.rkt{background:#bf0000}.btn.unx{background:#1b1f66}.btn.dmm{background:#0a74da}
.hero{padding:24px 0 8px}.hero h1{font-size:1.8rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px}.card h2{margin:0 0 8px;font-size:1.05rem;border:0;padding:0}.card h2 a{text-decoration:none}
.card ol{list-style:none;padding:0;margin:0}.card li{padding:3px 0;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.card .rk{display:inline-block;width:1.6em;font-size:1rem;margin-right:6px}
.more{font-size:.85rem}.svcgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px}.svc{background:var(--card);border-radius:10px;padding:8px 12px;font-size:.85rem}
.svc h3{margin:0 0 4px;font-size:.95rem}.svc ol{margin:0;padding-left:1.4em}ul.links{columns:2;padding-left:1.2em}
footer{border-top:1px solid var(--line);padding:16px;font-size:.78rem;color:var(--mu);text-align:center}
""")
# GitHub Pages 用
write(".nojekyll", "")
print("generated", len([f for _, _, fs in os.walk(OUT) for f in fs]), "files in docs/")
