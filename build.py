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

import re
COVERS = json.load(open(os.path.join(HERE, "covers.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "covers.json")) else {"by_id": {}, "by_title": {}}
def norm(t):
    return re.sub(r"[\s　:：・!！?？\-－~～「」『』()（）]", "", (t or "")).lower()
def cover(title=None, anilist_id=None, *alts):
    if anilist_id and str(anilist_id) in COVERS["by_id"]:
        return COVERS["by_id"][str(anilist_id)]
    for t in (title,) + alts:
        u = COVERS["by_title"].get(norm(t))
        if u: return u
    return None
def img(url, title, cls="cv"):
    if url:
        return '<img class="%s" src="%s" alt="%s" loading="lazy">' % (cls, esc(url), esc(title))
    return '<div class="%s noimg"></div>' % cls

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
    q = urllib.parse.quote_plus(title)
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

def yahoo_link(title):
    y = CFG.get("moshimo_yahoo")
    if not y: return None
    dest = "https://shopping.yahoo.co.jp/search?p=" + urllib.parse.quote(title)
    return ("https://af.moshimo.com/af/c/click?a_id=%s&p_id=%s&pc_id=%s&pl_id=%s&url=%s" %
            (y["a_id"], y["p_id"], y["pc_id"], y["pl_id"], urllib.parse.quote(dest, safe="")))

def shop_buttons(title):
    def a(cls, url, label, style=""):
        return '<a class="btn %s" %shref="%s" target="_blank" rel="nofollow sponsored noopener">%s</a>' % (
            cls, ('style="%s" ' % style) if style else "", esc(url), label)
    shops = [a("amz", amazon_link(title), "Amazon"), a("rkt", rakuten_link(title), "楽天")]
    if yahoo_link(title):
        shops.append(a("yho", yahoo_link(title), "Yahoo!"))
    html_ = ('<div class="shop"><span class="shop-lb">Blu-ray・原作・グッズを探す</span>'
             '<div class="shop-btns">%s</div></div>' % "".join(shops))
    vods = [a("vod", sv["url"], esc(sv["name"]), "--bc:%s" % esc(sv.get("color") or "#888"))
            for sv in CFG.get("streaming", []) if sv.get("url")]
    if vods:
        html_ += ('<div class="shop"><span class="shop-lb">配信で観る（無料体験あり）</span>'
                  '<div class="shop-btns">%s</div></div>' % "".join(vods))
    return html_

# ---------- ページ枠 ----------
NAV = [("index.html", "トップ"), ("now-japan.html", "国内いま人気"), ("now-world.html", "世界いま人気"),
       ("best-world.html", "歴代・世界評価"), ("netflix.html", "Netflix"), ("genre.html", "ジャンル別"),
       ("year.html", "年別")]

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
<meta property="og:type" content="website">
<meta property="og:site_name" content="%s">
<meta property="og:title" content="%s">
<meta property="og:image" content="%sthumbnail.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="%sstyle.css">
</head><body>
<header><a class="logo" href="%sindex.html">%s</a><nav>%s</nav></header>
<main>%s</main>
<footer>
<p>データ: AniList / Netflix Tudum 公式Top10 / JustWatch / Filmarks をもとに集計。作品画像は AniList より。最終更新 %s</p>
<p>本サイトはアフィリエイト広告（Amazonアソシエイト・楽天アフィリエイト等）を利用しています。</p>
<p><a href="%sabout.html">このサイトについて</a> ・ <a href="%sprivacy.html">プライバシーポリシー</a> ・ <a href="%s">お問い合わせ</a></p>
<p>&copy; %s</p>
</footer></body></html>""" % (esc(title), esc(site), esc(desc or title), esc(site), esc(title), esc(CFG["site_url"]), rel, rel, esc(site).replace("推し", "<b>推し</b>", 1), nav, body, TODAY,
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
        rows.append('<li><span class="rk">%s</span>%s<div class="body"><div class="tt">%s</div>'
                    '<div class="sub">%s</div>%s%s</div></li>' % (
                        esc(it["rank"]), img(it.get("img"), it["title"]), esc(it["title"]), esc(it.get("sub", "")),
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
# 日本のアニメではない作品（JustWatch の制作国表記で混入するもの）。Disney+ の欄だけは海外作品も表示する（2026-10-11 ユーザー指定）
EXCLUDE = {"ザ・スーパーマリオギャラクシー・ムービー", "The Legend of Korra",
           "Miraculous: Les aventures de Ladybug et Chat Noir", "Golden Axe",
           "The Super Mario Bros. Movie", "Zootopia 2", "Spider-Man"}
# 表記ゆれの修正
FIX_TITLE = {"そうそうのフリーレン": "葬送のフリーレン"}

def now_items(rows, n=30):
    out = []
    for r in rows:
        if len(out) >= n: break
        t = r.get("title_ja") or r.get("title")
        if r.get("original_title") and r.get("title"):
            t = r["title"]
        if t in EXCLUDE or r.get("title") in EXCLUDE or r.get("title_ja") in EXCLUDE: continue
        t = FIX_TITLE.get(t, t)
        sub = []
        if r.get("countries_in_top30"): sub.append("%s か国でTOP30入り" % r["countries_in_top30"])
        if r.get("top1_countries") and r["top1_countries"] != "0": sub.append("%s か国で1位" % r["top1_countries"])
        if r.get("year"): sub.append("%s年" % r["year"])
        if r.get("netflix_views"):
            try: sub.append("Netflix累計 %s万回再生" % format(int(float(r["netflix_views"])) // 10000, ","))
            except ValueError: pass
        out.append({"rank": len(out) + 1, "title": t, "sub": " / ".join(sub),
                    "img": cover(t, None, r.get("title"), r.get("title_ja"), r.get("original_title"))})
    return out

body = """<h1>国内いま人気のアニメ TOP30（全配信サービス合算）</h1>
<p class="lead">Netflix・Prime Video・U-NEXT・dアニメストア・Disney+・Hulu などの国内ランキングを合算した、いま日本で観られているアニメです（集計日 %s、毎月更新）。</p>
%s
<h2>Filmarks で話題のアニメ</h2>
<p class="lead">レビューサイト Filmarks の「話題のアニメ」。数字は5点満点の平均評価。</p>
%s""" % (esc(snap), rank_list(now_items(now_j)),
         rank_list([{"rank": r["rank"], "title": r["title"], "sub": "評価 %s / 5.0" % r["score_5"], "img": cover(r["title"])} for r in flm[:20]]))
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
        out.append({"rank": r.get("rank") or i, "title": jp_title(r), "sub": sub, "meta": genres_ja(r.get("genres")),
                    "img": cover(jp_title(r), r.get("anilist_id"), r.get("title_romaji"), r.get("title_english"))})
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
        t = r.get("anime_title_ja") or r["show_title"]
        out.append({"rank": r["rank"], "title": t, "sub": " / ".join(sub), "img": cover(t, None, r["show_title"])})
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

# ---------- 年別 ----------
by_year = collections.defaultdict(dict)
for r in seasonal:
    if is_adult(r) or not r.get("average_score"): continue
    try:
        y = int(r["year"]); pop = int(r["popularity"] or 0)
    except ValueError: continue
    if pop < (500 if y < 1990 else 2000): continue   # 古い年は作品数が少ないので基準を下げる
    if r["anilist_id"] not in by_year[y]:
        by_year[y][r["anilist_id"]] = r
year_links = collections.OrderedDict()
for y in sorted(by_year):
    rows = sorted(by_year[y].values(), key=lambda r: (-int(r["average_score"]), -int(r["popularity"] or 0)))[:30]
    if len(rows) < 5: continue
    fn = "year/%d.html" % y
    year_links.setdefault((y // 10) * 10, []).append('<a href="%s">%d年</a>' % (fn, y))
    prev_next = '<p class="pn">%s%s</p>' % (
        ('<a href="%d.html">← %d年</a>' % (y - 1, y - 1)) if (y - 1) in by_year else "",
        ('<a href="%d.html">%d年 →</a>' % (y + 1, y + 1)) if (y + 1) in by_year else "")
    b = "<h1>%d年のおすすめアニメ TOP%d</h1><p class=\"lead\">%d年に放送・公開された作品を世界評価（AniList スコア）順に。</p>%s%s%s" % (
        y, len(rows), y, prev_next, rank_list([dict(it, rank=i) for i, it in enumerate(anilist_items(rows, 30), 1)]), prev_next)
    write(fn, page("%d年のおすすめアニメ" % y, b, "%d年に放送されたアニメのおすすめランキングTOP%d" % (y, len(rows)), 1))
ydiv = "".join('<div class="yrow"><span class="ydec">%d年代</span><div class="ylinks">%s</div></div>' % (d, "".join(v))
               for d, v in sorted(year_links.items(), reverse=True))
write("year.html", page("年別おすすめアニメ", "<h1>年別おすすめアニメ</h1><p class=\"lead\">1970年から今年まで、その年に放送・公開されたアニメを世界評価順に紹介します。</p>%s" % ydiv,
                        "1970年から今年まで、年ごとのおすすめアニメランキング"))

# ---------- トップ ----------
def mini(items, href, title):
    lis = "".join('<li><span class="rk">%s</span>%s<span class="nm">%s</span></li>' % (esc(i["rank"]), img(i.get("img"), i["title"], "cvs"), esc(i["title"])) for i in items[:5])
    return '<section class="card"><h2><a href="%s">%s</a></h2><ol>%s</ol><a class="more" href="%s">続きを見る →</a></section>' % (href, esc(title), lis, href)

SVC_ICON = {"Netflix": "nfx", "Amazon Prime Video": "amp", "Disney+": "dnp", "Crunchyroll": "cru",
            "Hulu": "hlu", "HBO Max": "mxx", "Apple TV+": "atp"}
import shutil
if os.path.isdir(os.path.join(HERE, "assets", "svc")):
    shutil.copytree(os.path.join(HERE, "assets", "svc"), os.path.join(OUT, "svc"), dirs_exist_ok=True)
svc_cards = ""
HIDE_SVC = {"Apple TV+"}  # アニメ作品がほぼ無いので表示しない（2026-10-12 ユーザー指定）
for s, rows in by_svc.items():
    if s in HIDE_SVC: continue
    ic = SVC_ICON.get(s)
    head = ('<img class="svc-ic" src="svc/%s.png" alt="" width="28" height="28">' % ic if ic else "") + esc(s)
    picks = [x for x in rows if s == "Disney+" or (x["title"] not in EXCLUDE and x.get("title_ja") not in EXCLUDE)][:5]
    def nm(r): return FIX_TITLE.get(r.get("title_ja") or r["title"], r.get("title_ja") or r["title"])
    svc_cards += '<div class="svc"><h3>%s</h3><ol>%s</ol></div>' % (
        head, "".join('<li><span class="rk">%d</span>%s<span class="nm">%s</span></li>' % (
            n, img(cover(r.get("title_ja"), None, r["title"]), nm(r), "cvs"), esc(nm(r))) for n, r in enumerate(picks, 1)))

HERO_IMG = os.path.exists(os.path.join(OUT, "thumbnail.jpg"))
body = (("""<section class="hero hero-img"><h1 class="vh">%s</h1>
<img src="thumbnail.jpg" alt="推しアニメランキング｜世界27か国・国内12サービスの配信ランキングと歴代評価から、いま観るべきアニメがわかる" width="1200" height="630">
<p class="vh">世界27か国・国内12サービスの配信ランキングと、歴代の評価データから「いま観るべきアニメ」を毎月更新で紹介します。</p></section>""" if HERO_IMG else
"""<section class="hero"><h1>%s</h1>
<p>世界27か国・国内12サービスの配信ランキングと、歴代の評価データから「いま観るべきアニメ」を毎月更新で紹介します。</p></section>""") + """
<div class="grid">%s%s%s%s</div>
<h2>配信サービス別 世界TOP5</h2><div class="svcgrid">%s</div>
<h2>探す</h2><p class="find"><a href="genre.html">ジャンル別のおすすめ →</a></p><p class="find"><a href="year.html">年別のおすすめ（1970年〜）→</a></p>
""") % (esc(CFG["site_name"]),
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
<ul><li>AniList（世界最大級のアニメデータベース）: 歴代評価・ジャンル・年別</li>
<li>Netflix Tudum 公式 Top 10: 週間ランキング・再生回数</li>
<li>JustWatch: 各国・各配信サービスの人気ランキング</li>
<li>Filmarks: 話題のアニメ・5段階評価</li></ul>
<p>配信サービスのアイコンは JustWatch より。</p>
<h2>運営者</h2><p>Masabee（YouTube: <a href="https://www.youtube.com/@Masabee1029" target="_blank" rel="noopener">@Masabee1029</a>）</p>
<h2>お問い合わせ</h2><p>%s</p>
<h2>広告について</h2><p>当サイトは Amazon.co.jp アソシエイト、楽天アフィリエイト、もしもアフィリエイト（Yahoo!ショッピング等）のアフィリエイトプログラムに参加しています。リンク先での購入・契約により当サイトに紹介料が支払われることがありますが、ランキングの順位は収益によって変わりません。</p>
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
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.8}
a{color:var(--ac)}header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 24px;padding:16px 20px;border-bottom:1px solid var(--line);background:var(--card)}
.logo{font-weight:800;font-size:1.75rem;letter-spacing:.02em;line-height:1.3;text-decoration:none;color:var(--tx)}.logo b{color:var(--ac)}nav{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.9rem}nav a{text-decoration:none;color:var(--mu)}nav a:hover{color:var(--ac)}
.pr{font-size:.75rem;color:var(--mu);margin:6px 16px}main{max-width:860px;margin:0 auto;padding:8px 16px 40px}
h1{font-size:1.5rem;margin:16px 0 8px}h2{font-size:1.2rem;margin:40px 0 12px;border-left:4px solid var(--ac);padding-left:8px}.lead{color:var(--mu);font-size:.95rem;margin:0 0 20px}
ol.rank{list-style:none;padding:0;margin:0}ol.rank li{display:flex;gap:16px;padding:20px 0;border-bottom:1px solid var(--line)}
.rk{flex:0 0 2.2em;font-size:1.4rem;font-weight:800;color:var(--ac);text-align:right}ol.rank li:nth-child(-n+3) .rk{color:#ffd166}
.cv{flex:0 0 72px;width:72px;height:102px;object-fit:cover;border-radius:6px;background:#222}.noimg{background:linear-gradient(135deg,#262a33,#1a1d24)}
.cvs{display:inline-block;width:28px;height:40px;object-fit:cover;border-radius:3px;vertical-align:middle;margin-right:6px;background:#222}
.body{flex:1;min-width:0}.tt{font-weight:700;font-size:1.05rem;line-height:1.5;margin-bottom:4px}.sub,.meta{font-size:.82rem;color:var(--mu);line-height:1.7}
.shop{margin-top:12px}.shop-lb{display:block;font-size:.72rem;color:var(--mu);margin-bottom:4px;letter-spacing:.02em}
.shop-btns{display:flex;flex-wrap:wrap;gap:8px}
.btn{--bc:#888;font-size:.75rem;padding:3px 12px;border-radius:999px;text-decoration:none;background:#000;color:var(--bc);border:1px solid var(--bc);transition:background .15s}
.btn:hover{background:#1a1a1a}
.btn.amz{--bc:#ff9900}.btn.rkt{--bc:#ff4d4d}.btn.yho{--bc:#ff4d6d}
.hero{padding:24px 0 8px}.hero h1{font-size:1.8rem}.hero-img{padding:20px 0 12px}.hero-img img{display:block;width:100%;height:auto;border-radius:14px;border:1px solid var(--line)}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}@media(max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px}.card h2{margin:0 0 8px;font-size:1.05rem;border:0;padding:0}.card h2 a{text-decoration:none}
.card ol{list-style:none;padding:0;margin:0}.card li{padding:6px 0;font-size:.92rem;line-height:1.5;display:flex;align-items:center;gap:2px}.nm{flex:1;min-width:0;overflow-wrap:anywhere}.card .rk{display:inline-block;width:1.6em;font-size:1rem;margin-right:4px;flex:0 0 auto}.cvs{flex:0 0 auto}
.more{display:inline-block;margin-top:8px;font-size:.85rem}.svcgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.svc{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-size:.88rem}
.svc h3{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:1rem}.svc-ic{width:28px;height:28px;border-radius:7px}.svc ol{list-style:none;margin:0;padding:0}.svc li{display:flex;align-items:center;gap:2px;padding:5px 0;line-height:1.5}.svc .rk{display:inline-block;width:1.6em;font-size:.95rem;margin-right:4px;flex:0 0 auto}
.find{margin:6px 0}.find a{font-size:1rem}.pn{display:flex;justify-content:space-between;font-size:.9rem;margin:12px 0}
.yrow{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid var(--line);align-items:baseline}.ydec{flex:0 0 5em;font-weight:700;color:var(--mu)}.ylinks{display:flex;flex-wrap:wrap;gap:6px 14px}
footer{border-top:1px solid var(--line);padding:16px;font-size:.78rem;color:var(--mu);text-align:center}
""")
# GitHub Pages 用
write(".nojekyll", "")
print("generated", len([f for _, _, fs in os.walk(OUT) for f in fs]), "files in docs/")
