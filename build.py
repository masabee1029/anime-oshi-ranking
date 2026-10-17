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
def strip_extra(t):
    """【規制解除版】（日本語吹替版）第4期 2nd Season 全7章 などの付け足しを外す"""
    t = re.sub(r"[【\[（(「『].*?[】\]）)」』]", " ", t or "")
    t = re.sub(r"(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*\d+|全\s*\d+\s*章|劇場版)", " ", t)
    return t.strip(" 　")
def cover(title=None, anilist_id=None, *alts):
    if anilist_id and str(anilist_id) in COVERS["by_id"]:
        return COVERS["by_id"][str(anilist_id)]
    for t in (title,) + alts:
        u = COVERS["by_title"].get(norm(t))
        if u: return u
    for t in (title,) + alts:
        u = COVERS["by_title"].get(norm(strip_extra(t)))
        if u: return u
    return None
import hashlib
TILE_COLORS = [("#ff6b9d", "#7a2e5c"), ("#ffd166", "#8a5a12"), ("#6ea8ff", "#25407a"), ("#7ee0b5", "#1f6b52"),
               ("#c39bff", "#4e2f86"), ("#ff9f6b", "#8a3d1c"), ("#5fd4e8", "#1a5f6e"), ("#ff7a7a", "#7a2323")]
def tile(title, cls):
    """作品の絵の代わりに、題名の頭文字を使ったオリジナルの色タイル"""
    t = re.sub(r"^[\s「『【（(\[]+", "", title or "?")
    ch = t[:1] if t else "?"
    h = int(hashlib.md5((title or "").encode("utf-8")).hexdigest(), 16) % len(TILE_COLORS)
    c1, c2 = TILE_COLORS[h]
    return '<div class="%s tile" style="background:linear-gradient(140deg,%s,%s)" aria-hidden="true"><span>%s</span></div>' % (cls, c1, c2, esc(ch))
def img(url, title, cls="cv"):
    if url and CFG.get("use_anilist_covers"):
        return '<img class="%s" src="%s" alt="%s" loading="lazy">' % (cls, esc(url), esc(title))
    return tile(title, cls)

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
NAV = [("index.html", "トップ"), ("season.html", "今季アニメ"), ("prev-season.html", "前季アニメ"), ("seasons.html", "シーズン別"), ("now-japan.html", "国内いま人気"), ("now-world.html", "世界いま人気"),
       ("best-world.html", "歴代・世界評価"), ("netflix.html", "Netflix"), ("services.html", "配信サービス別"), ("country.html", "国別"), ("genre.html", "ジャンル別"),
       ("year.html", "年別")]

GA_ID = (CFG.get("ga_measurement_id") or "").strip()
GA_TAG = ("""<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','%s');</script>
""" % (GA_ID, GA_ID)) if re.fullmatch(r"G-[A-Z0-9]+", GA_ID) else ""

BANNERS = set(f[:-4] for f in os.listdir(os.path.join(HERE, "assets", "banner")) if f.endswith(".jpg")) if os.path.isdir(os.path.join(HERE, "assets", "banner")) else set()
# 今季アニメの画像は季節ごとに assets/banner/season-<年>-<winter|spring|summer|fall>.jpg を置く（無い季節はトップの画像）
# ---------- 収益ブログ型の共通パーツ（サイドバー・パンくず・著者・シェア・構造化データ） ----------
SISTER_SITES = [("AIデザイン実践ラボ", "ai-design-lab"), ("推し活グッズ＆遠征ガイド", "oshikatsu-guide"),
                ("はじめてのスパイスカレー", "spice-curry-start"), ("推し発見ナビ", "oshi-hakken-navi"),
                ("そのまま使えるAIプロンプト集", "ai-prompt-recipes")]
PROFILE = ("アニメ好きの運営者が、Netflix 公式 Top10・JustWatch・AniList・Filmarks のデータを毎月集計して、"
           "「いま観るべきアニメ」が一目でわかるランキングにまとめています。歌い手やボカロなど音楽の推し活もしています。")

def sidebar(rel):
    rank = "".join('<li><a href="%s%s">%s</a></li>' % (rel, h, t) for h, t in NAV[1:])
    svc = "".join('<a class="sbtn" rel="nofollow sponsored noopener" target="_blank" href="%s" style="--bc:%s">%s</a>'
                  % (esc(x["url"]), esc(x.get("color", "#ff6b9d")), esc(x["name"])) for x in CFG.get("streaming", []) if x.get("url"))
    sis = "".join('<li><a href="https://masabee1029.github.io/%s/" target="_blank" rel="noopener">%s</a></li>' % (p, esc(n)) for n, p in SISTER_SITES)
    return ('<aside class="side">'
            '<div class="sbox"><div class="sh">運営者</div><div class="prof"><div class="avatar">推</div><p>%s</p></div>'
            '<a class="more" href="%sabout.html">このサイトについて</a></div>'
            '%s'
            '<div class="sbox"><div class="sh">ランキング一覧</div><ul class="slist">%s</ul></div>'
            '<div class="sbox"><div class="sh">姉妹サイト</div><ul class="slist">%s</ul></div>'
            '</aside>') % (esc(PROFILE), rel,
                           ('<div class="sbox sticky"><div class="sh">アニメを観るなら <span class="prc">PR</span></div>%s'
                            '<p class="note">配信作品・料金・無料期間は各サービスの公式サイトで確認してください。</p></div>' % svc) if svc else "",
                           rank, sis)

def author_box(rel):
    return ('<div class="author"><div class="avatar">推</div><div><strong>このページを作った人：運営者</strong><p>%s</p>'
            '<p><a href="%sabout.html">運営者について詳しく</a></p></div></div>' % (esc(PROFILE), rel))

def share_box():
    return ('<div class="share"><a class="sx" rel="noopener" target="_blank" href="https://twitter.com/intent/tweet?url=\x00URLQ\x00&text=\x00TITLEQ\x00">Xでシェア</a>'
            '<a class="sl" rel="noopener" target="_blank" href="https://social-plugins.line.me/lineit/share?url=\x00URLQ\x00">LINEで送る</a>'
            '<a class="sb" rel="noopener" target="_blank" href="https://b.hatena.ne.jp/entry/panel/?url=\x00URLQ\x00">はてブ</a></div>')

def page(title, body, desc="", path_depth=0, banner=None, hero=False):
    """banner: ページ用サムネイル名（assets/banner/<name>.jpg）。hero=True でページ上部にも表示"""
    rel = "../" * path_depth
    og_img = ("banner/%s.jpg" % banner) if banner in BANNERS else "thumbnail.jpg"
    if hero and banner in BANNERS:
        body = ('<p class="page-hero"><img src="%sbanner/%s.jpg" alt="%s" width="1200" height="630"></p>' % (rel, banner, esc(title))) + body
    nav = "".join('<a href="%s%s">%s</a>' % (rel, h, t) for h, t in NAV)
    site = CFG["site_name"]
    is_top = title == "トップ"
    is_fixed = title in ("このサイトについて", "プライバシーポリシー")
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": site, "url": CFG["site_url"]} if is_top else \
         {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "トップ", "item": CFG["site_url"]},
             {"@type": "ListItem", "position": 2, "name": title}]}
    if not is_top and 'class="crumb"' not in body:
        body = '<p class="crumb"><a href="%sindex.html">トップ</a> › %s</p>' % (rel, esc(title)) + body
    if not is_fixed:
        body += share_box() + author_box(rel)
    body = '<div class="layout"><main>%s</main>%s</div>' % (body, sidebar(rel))
    ld_tag = '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False)

    contact = CFG.get("contact_url") or (rel + "about.html")
    return """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s | %s</title>
<meta name="description" content="%s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%s">
<meta property="og:title" content="%s">
<meta property="og:image" content="%s%s">
<meta name="twitter:card" content="summary_large_image">
%s%s%s<link rel="stylesheet" href="%sstyle.css">
</head><body>
<header><a class="logo" href="%sindex.html">%s</a><nav>%s</nav></header>
<p class="pr">※本サイトはプロモーション（広告）を含みます。商品・配信サービスのリンクから購入・登録されると運営者に紹介料が入ることがあります。</p>
%s
<footer>
<p>データ: AniList / Netflix Tudum 公式Top10 / JustWatch / Filmarks をもとに集計。最終更新 %s</p>
<p>本サイトはアフィリエイト広告（Amazonアソシエイト・楽天アフィリエイト等）を利用しています。</p>
<p><a href="%sabout.html">このサイトについて</a> ・ <a href="%sprivacy.html">プライバシーポリシー</a> ・ <a href="%s">お問い合わせ</a></p>
<p>&copy; %s</p>
</footer></body></html>""" % (esc(title), esc(site), esc(desc or title), esc(site), esc(title), esc(CFG["site_url"]), og_img,
       ('<meta name="google-site-verification" content="%s">\n' % esc(CFG["google_site_verification"])) if CFG.get("google_site_verification") else "",
       GA_TAG, ld_tag, rel, rel, esc(site).replace("推し", "<b>推し</b>", 1), nav, body, TODAY,
                              rel, rel, esc(contact), esc(site))

PAGES = collections.OrderedDict()
def write(name, content):
    """いったん溜めて、最後に作品名を個別ページへのリンクに変えてから書き出す"""
    PAGES[name] = content

def flush():
    pat = re.compile("\x00L([0-9a-f]+)\x00(.*?)\x00E", re.S)
    for name, content in PAGES.items():
        rel = "../" * name.count("/")
        def sub(m):
            k, text = m.group(1), m.group(2)
            if k in TITLE_PAGES:
                return '<a class="tl" href="%sanime/%s.html">%s</a>' % (rel, k, text)
            return text
        content = pat.sub(sub, content)
        if name.endswith(".html"):
            url = CFG["site_url"].rstrip("/") + "/" + ("" if name == "index.html" else name)
            mt = re.search(r"<title>(.*?)</title>", content)
            content = content.replace("\x00URLQ\x00", urllib.parse.quote(url, safe="")).replace(
                "\x00TITLEQ\x00", urllib.parse.quote(html.unescape(mt.group(1)) if mt else ""))
        p = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

# ---------- 作品の記録（個別ページ用） ----------
def tkey(title):
    return hashlib.md5(norm(FIX_TITLE.get(title, title)).encode("utf-8")).hexdigest()[:10]
TITLE_DB = collections.OrderedDict()   # key -> {"title", "apps": [(label, rank, href, sub)], "alts": set()}
TITLE_PAGES = set()
def register(title, label, rank, href, sub="", alts=()):
    k = tkey(title)
    d = TITLE_DB.setdefault(k, {"title": title, "apps": [], "alts": set()})
    if not any(a[0] == label for a in d["apps"]):
        d["apps"].append((label, rank, href, sub))
    d["alts"].update(a for a in alts if a)
    TITLE_PAGES.add(k)
def tlink(title):
    """作品名に目印を付ける（個別ページがあれば最後にリンクになる）"""
    return "\x00L%s\x00%s\x00E" % (tkey(title), esc(title))

KAKUGEN = read_json(os.path.join(HERE, "kakugen.json")) if os.path.exists(os.path.join(HERE, "kakugen.json")) else {}
WATCH = read_json(os.path.join(HERE, "watch.json")) if os.path.exists(os.path.join(HERE, "watch.json")) else {}
PV = read_json(os.path.join(HERE, "pv.json")) if os.path.exists(os.path.join(HERE, "pv.json")) else {}
def kg_norm(t):
    t = re.sub(r"^(新劇場版|劇場版|映画)\s*", "", t or "")
    t = re.sub(r"[「」『』【】〈〉\s　:：・!！?？\-－~～()（）]", "", t)
    return t.lower()
KG_KEYS = sorted(((kg_norm(k), v) for k, v in KAKUGEN.items() if not k.startswith("_")), key=lambda kv: -len(kv[0]))
def kakugen(title):
    """作中の名言 {"q", "who"}。作品名の頭が一致する一番長いキー（exact のものは題名が完全一致のときだけ）"""
    t = kg_norm(FIX_TITLE.get(title, title))
    for k, v in KG_KEYS:
        if len(k) < 2: continue
        if (v.get("exact") and t == k) or (not v.get("exact") and t.startswith(k)):
            return v
    return None
def quote_html(kg, cls):
    if kg.get("original"):
        return '<div class="%s orig">%s<span class="kgw">— 当サイトオリジナル</span></div>' % (cls, esc(kg["q"]))
    return '<div class="%s">「%s」<span class="kgw">— %s</span></div>' % (cls, esc(kg["q"]), esc(kg["who"]))

# ---------- 順位の変動（前回の記録と比べる） ----------
HIST = os.path.join(ST, "history")
def prev_rows(fname, cur_date):
    """cur_date より前で、fname を含む一番新しい記録を返す。無ければ None"""
    if not os.path.isdir(HIST): return None
    for d in sorted(os.listdir(HIST), reverse=True):
        if d < cur_date and os.path.exists(os.path.join(HIST, d, fname)):
            return read_csv(os.path.join(HIST, d, fname))
    return None
def prev_map(fname, cur_date, keyfn, filt=lambda r: True):
    rows = prev_rows(fname, cur_date)
    if rows is None: return None
    out = {}
    for r in rows:
        if filt(r):
            try: out.setdefault(keyfn(r), int(r["rank"]))
            except (ValueError, KeyError): pass
    return out
def chg_badge(cur, key, prev):
    if prev is None: return ""
    if key not in prev: return '<span class="chg new">NEW</span>'
    d = prev[key] - int(cur)
    if d > 0: return '<span class="chg up">↑%d</span>' % d
    if d < 0: return '<span class="chg dn">↓%d</span>' % -d
    return '<span class="chg eq">→</span>'

def watch_line(title):
    w = WATCH.get(tkey(title))
    if not w or not w.get("flatrate"): return ""
    names = w["flatrate"]
    return '<div class="watch">見放題%s: %s%s</div>' % ("（シリーズ）" if w.get("series") else "", esc("・".join(names[:4])), " ほか" if len(names) > 4 else "")

def rank_list(items, show_shop=True, label=None, href=None):
    """items: list of dict(rank,title,sub,meta,chg)。label を渡すと作品の個別ページに記録する"""
    rows = []
    for it in items:
        if label:
            register(it["title"], label, it["rank"], href, it.get("sub", ""), it.get("alts", ()))
        kg = kakugen(it["title"])
        rows.append('<li><span class="rk">%s%s</span>%s<div class="body"><div class="tt">%s</div>'
                    '<div class="sub">%s</div>%s%s%s%s</div></li>' % (
                        esc(it["rank"]), it.get("chg", ""), img(it.get("img"), it["title"]), tlink(it["title"]), esc(it.get("sub", "")),
                        ('<div class="meta">%s</div>' % esc(it["meta"])) if it.get("meta") else "",
                        quote_html(kg, "kg") if kg else "",
                        watch_line(it["title"]),
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
PREV_J = prev_map("japan_allservices_ranking.csv", snap, lambda r: r["title"])
PREV_W = prev_map("world_allservices_ranking.csv", snap, lambda r: r["title"])
PREV_F = prev_map("filmarks_trend_anime.csv", snap, lambda r: r["title"])
PREV_NG = prev_map("netflix_anime_ranking_global.csv", snap, lambda r: r["show_title"])
PREV_NJ = prev_map("netflix_anime_ranking_by_country.csv", snap, lambda r: r["show_title"], lambda r: r["country"] == "JP")
PREV_SVC = prev_map("world_by_service_ranking.csv", snap, lambda r: (r["service"], r["title"]))
PREV_JW = prev_map("justwatch_anime_by_country_service.csv", snap, lambda r: (r["country"], r["service"], r["original_title"] or r["title"]))

def is_adult(r):
    return "Hentai" in (r.get("genres") or "")
world = [r for r in world if not is_adult(r)]

# ---------- 国内いま人気 ----------
# 日本のアニメではない作品（JustWatch の制作国表記で混入するもの）。Disney+ の欄だけは海外作品も表示する（2026-10-11 ユーザー指定）
EXCLUDE = {"ザ・スーパーマリオギャラクシー・ムービー", "The Legend of Korra",
           "Miraculous: Les aventures de Ladybug et Chat Noir", "Golden Axe",
           "The Super Mario Bros. Movie", "Zootopia 2", "Spider-Man",
           "The Super Mario Galaxy Movie", "スーパーマン", "Superman", "ThunderCats", "The Secret Saturdays",
           "The Bad Guys 2", "Trolls Band Together", "Sonic the Hedgehog 3", "The Boss Baby: Family Business",
           "Kung Fu Panda 4", "Il était une fois... la vie", "Transformers"}
# 表記ゆれの修正
FIX_TITLE = {"そうそうのフリーレン": "葬送のフリーレン"}

def now_items(rows, n=30, prev=None):
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
                    "img": cover(t, None, r.get("title"), r.get("title_ja"), r.get("original_title")),
                    "chg": chg_badge(r["rank"], r.get("title"), prev),
                    "alts": (r.get("title"), r.get("title_ja"), r.get("original_title"))})
    return out

body = """<h1>国内いま人気のアニメ TOP30（全配信サービス合算）</h1>
<p class="lead">Netflix・Prime Video・U-NEXT・dアニメストア・Disney+・Hulu などの国内ランキングを合算した、いま日本で観られているアニメです（集計日 %s、毎月更新）。</p>
%s
<h2>Filmarks で話題のアニメ</h2>
<p class="lead">レビューサイト Filmarks の「話題のアニメ」。数字は5点満点の平均評価。</p>
%s""" % (esc(snap), rank_list(now_items(now_j, prev=PREV_J), label="国内いま人気（全配信合算）", href="now-japan.html"),
         rank_list([{"rank": r["rank"], "title": r["title"], "sub": "評価 %s / 5.0" % r["score_5"], "img": cover(r["title"]),
                     "chg": chg_badge(r["rank"], r["title"], PREV_F)} for r in flm[:20]], label="Filmarks 話題のアニメ", href="now-japan.html"))
write("now-japan.html", page("国内いま人気のアニメ TOP30", body, "日本の配信サービス全体で今月人気のアニメランキング", banner="now-japan", hero=True))

body = """<h1>世界いま人気のアニメ TOP30（27か国・全配信合算）</h1>
<p class="lead">世界27か国の Netflix・Prime Video・Disney+・Crunchyroll・Hulu・HBO Max・Apple TV+ のランキングを合算（集計日 %s）。</p>
%s""" % (esc(snap), rank_list(now_items(now_w, prev=PREV_W), label="世界いま人気（27か国合算）", href="now-world.html"))
write("now-world.html", page("世界いま人気のアニメ TOP30", body, "世界27か国の配信ランキングを合算した今月のアニメ人気TOP30", banner="now-world", hero=True))

# ---------- 歴代・世界評価 ----------
def anilist_items(rows, n=100):
    out = []
    for i, r in enumerate(rows[:n], 1):
        sub = "評価 %s点 / %s / %s年 %s" % (r.get("average_score") or r.get("mean_score"), r.get("format"),
                                         r.get("season_year"), r.get("studio") or "")
        out.append({"rank": r.get("rank") or i, "title": jp_title(r), "sub": sub, "meta": genres_ja(r.get("genres")),
                    "img": cover(jp_title(r), r.get("anilist_id"), r.get("title_romaji"), r.get("title_english")),
                    "alts": (r.get("title_romaji"), r.get("title_english"))})
    return out

body = """<h1>歴代アニメ 世界評価ランキング TOP100</h1>
<p class="lead">世界最大級のアニメデータベース AniList の平均スコア順。海外ファンからの評価の高さを示します。</p>
%s""" % rank_list(anilist_items(world), label="歴代・世界評価", href="best-world.html")
write("best-world.html", page("歴代アニメ 世界評価ランキング TOP100", body, "AniList 平均スコアによる歴代アニメ世界評価TOP100", banner="best-world", hero=True))

# ---------- Netflix ----------
def nf_items(rows, n=30, views=True, prev=None):
    out = []
    for r in rows[:n]:
        sub = ["TOP10入り %s週" % r["weeks"], "最高 %s位" % r["best"]]
        if views and r.get("views"):
            sub.append("累計 %s万回再生" % format(int(float(r["views"])) // 10000, ","))
        t = r.get("anime_title_ja") or r["show_title"]
        out.append({"rank": r["rank"], "title": t, "sub": " / ".join(sub), "img": cover(t, None, r["show_title"]),
                    "chg": chg_badge(r["rank"], r["show_title"], prev), "alts": (r["show_title"],)})
    return out

body = """<h1>Netflix アニメランキング</h1>
<h2>世界 TOP30（公式週間TOP10の累計）</h2>
<p class="lead">Netflix 公式「Tudum Top 10」の世界集計。再生回数は Netflix が公表している唯一の公式数字です。</p>
%s
<h2>日本 TOP30</h2>
<p class="lead">日本の Netflix 週間TOP10に入った週数の多い順。</p>
%s""" % (rank_list(nf_items(nf_g, prev=PREV_NG), label="Netflix 世界", href="netflix.html"),
         rank_list(nf_items(nf_c, views=False, prev=PREV_NJ), label="Netflix 日本", href="netflix.html"))
write("netflix.html", page("Netflix アニメランキング 世界・日本", body, "Netflix公式Top10に基づくアニメの世界・日本ランキング", banner="netflix", hero=True))


# ---------- 配信サービス別・国別 ----------
jw = read_csv(os.path.join(ST, "justwatch_anime_by_country_service.csv"))
JA_MAP = {}
for r in now_w + svc:
    JA_MAP.setdefault(r["title"], r.get("title_ja") or r["title"])
COUNTRY_JA = {"AE": "アラブ首長国連邦", "AR": "アルゼンチン", "AU": "オーストラリア", "BR": "ブラジル", "CA": "カナダ",
              "DE": "ドイツ", "ES": "スペイン", "FR": "フランス", "GB": "イギリス", "HK": "香港", "ID": "インドネシア",
              "IN": "インド", "IT": "イタリア", "JP": "日本", "KR": "韓国", "MX": "メキシコ", "MY": "マレーシア",
              "NL": "オランダ", "PH": "フィリピン", "PL": "ポーランド", "SA": "サウジアラビア", "SE": "スウェーデン",
              "SG": "シンガポール", "TH": "タイ", "TR": "トルコ", "TW": "台湾", "US": "アメリカ"}
REGION = [("アジア", ["JP", "KR", "TW", "HK", "TH", "ID", "MY", "SG", "PH", "IN"]),
          ("北米・中南米", ["US", "CA", "MX", "BR", "AR"]),
          ("ヨーロッパ", ["GB", "FR", "DE", "ES", "IT", "NL", "SE", "PL", "TR"]),
          ("中東・オセアニア", ["AE", "SA", "AU"])]

def jw_title(r):
    key = r["original_title"] or r["title"]
    if r["country"] == "JP":
        t = r["title"]
        if not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", t):
            t = JA_MAP.get(key, t)
    else:
        t = JA_MAP.get(key) or (r["original_title"] if re.search(r"[\u3040-\u30ff]", r["original_title"] or "") else r["title"])
    return FIX_TITLE.get(t, t)

def jw_items(rows, n=30, allow_foreign=False):
    # 変動は raw の順位で比べる
    out = []
    for r in sorted(rows, key=lambda r: int(r["rank"])):
        if len(out) >= n: break
        t = jw_title(r)
        if not allow_foreign and (t in EXCLUDE or r["title"] in EXCLUDE or r["original_title"] in EXCLUDE): continue
        sub = ("%s年" % r["year"]) if r.get("year") else ""
        out.append({"rank": len(out) + 1, "title": t, "sub": sub,
                    "img": cover(t, None, r["original_title"], r["title"], JA_MAP.get(r["original_title"] or r["title"])),
                    "chg": chg_badge(r["rank"], (r["country"], r["service"], r["original_title"] or r["title"]), PREV_JW),
                    "alts": (r["original_title"], r["title"])})
    return out

def simple_items(rows, n=30, fname=None):
    prev = prev_map(fname, rows[0]["snapshot_date"], lambda r: r["title"]) if (fname and rows) else None
    out = []
    for r in rows[:n]:
        t = FIX_TITLE.get(r["title"], r["title"])
        out.append({"rank": len(out) + 1, "title": t, "sub": "", "img": cover(t), "chg": chg_badge(r["rank"], r["title"], prev)})
    return out

# 世界（27か国合算）のサービス
WORLD_SVC = [("nfx", "Netflix"), ("amp", "Amazon Prime Video"), ("dnp", "Disney+"), ("cru", "Crunchyroll"),
             ("hlu", "Hulu"), ("mxx", "HBO Max")]
# 国内のサービス: (id, 表示名, データの取り方)
JP_SVC = [("nfx", "Netflix", ("jw", "Netflix")), ("amp", "Amazon Prime Video", ("jw", "Amazon Prime Video")),
          ("dnp", "Disney+", ("jw", "Disney+")), ("hlu", "Hulu", ("jw", "Hulu")),
          ("unext", "U-NEXT", ("jw", "U-NEXT")), ("danime", "dアニメストア", ("jw", "dアニメストア（Amazon チャンネル）")),
          ("fod", "FOD", ("jw", "FOD")), ("abema", "ABEMA", ("csv", "abema")), ("dmmtv", "DMM TV", ("csv", "dmmtv")),
          ("tver", "TVer", ("csv", "tver")), ("bandai", "バンダイチャンネル", ("csv", "bandai"))]

def jp_rows(how):
    kind, key = how
    if kind == "jw":
        return jw_items([r for r in jw if r["country"] == "JP" and r["service"] == key], 30, key == "Disney+")
    path = os.path.join(ST, "%s_anime_ranking.csv" % key)
    return simple_items(read_csv(path), fname="%s_anime_ranking.csv" % key) if os.path.exists(path) else []

SVC_ICON_FILE = {"nfx": "nfx", "amp": "amp", "dnp": "dnp", "cru": "cru", "hlu": "hlu", "mxx": "mxx",
                 "unext": "unext", "abema": "abema", "tver": "tver", "fod": "fod"}
hub_world, hub_jp = [], []
jp_map = {sid: (name, how) for sid, name, how in JP_SVC}
for sid, name in WORLD_SVC:
    rows = [r for r in svc if r["service"] == name]
    world_list = []
    for r in rows:
        t = FIX_TITLE.get(r.get("title_ja") or r["title"], r.get("title_ja") or r["title"])
        if sid != "dnp" and (t in EXCLUDE or r["title"] in EXCLUDE): continue
        if len(world_list) >= 30: break
        world_list.append({"rank": len(world_list) + 1, "title": t,
                           "sub": "%s か国でTOP30入り" % r["countries_in_top30"], "img": cover(r.get("title_ja"), None, r["title"]),
                           "chg": chg_badge(r["rank"], (name, r["title"]), PREV_SVC), "alts": (r["title"],)})
    body = "<h1>%s アニメランキング</h1>" % esc(name)
    body += "<h2>世界 TOP%d（27か国合算）</h2><p class=\"lead\">各国の%sアニメランキングを点数化（1位=30点…30位=1点）して合計。</p>%s" % (
        len(world_list), esc(name), rank_list(world_list, label="%s 世界" % name, href="service/%s.html" % sid))
    if sid in jp_map:
        jl = jp_rows(jp_map[sid][1])
        if jl: body += "<h2>日本 TOP%d</h2>%s" % (len(jl), rank_list(jl, label="%s 日本" % name, href="service/%s.html" % sid))
    write("service/%s.html" % sid, page("%s アニメランキング 世界・日本" % name, body, "%sで人気のアニメランキング（世界27か国合算・日本）" % name, 1, banner="services"))
    hub_world.append((sid, name, world_list[:3]))
for sid, name, how in JP_SVC:
    if sid in dict(WORLD_SVC): 
        hub_jp.append((sid, name, jp_rows(how)[:3])); continue
    jl = jp_rows(how)
    if not jl: continue
    body = "<h1>%s アニメランキング</h1><h2>日本 TOP%d</h2>%s" % (esc(name), len(jl), rank_list(jl, label="%s 日本" % name, href="service/%s.html" % sid))
    write("service/%s.html" % sid, page("%s アニメランキング" % name, body, "%sで人気のアニメランキング" % name, 1, banner="services"))
    hub_jp.append((sid, name, jl[:3]))

def hub_card(sid, name, top):
    icon = SVC_ICON_FILE.get(sid)
    h = ('<img class="svc-ic" src="svc/%s.png" alt="" width="28" height="28">' % icon if icon else '<span class="svc-ic txt">%s</span>' % esc(name[:1])) + esc(name)
    lis = "".join('<li><span class="rk">%d</span>%s<span class="nm">%s</span></li>' % (i["rank"], img(i.get("img"), i["title"], "cvs"), esc(i["title"])) for i in top)
    return '<a class="svc svc-link" href="service/%s.html"><h3>%s</h3><ol>%s</ol><span class="more">ランキングを見る →</span></a>' % (sid, h, lis)

body = ("<h1>配信サービス別アニメランキング</h1><p class=\"lead\">各配信サービスで、いま人気のアニメ。毎月更新（集計日 %s）。</p>" % esc(snap) +
        "<h2>世界（27か国合算）</h2><div class=\"svcgrid\">%s</div>" % "".join(hub_card(*x) for x in hub_world) +
        "<h2>日本国内</h2><div class=\"svcgrid\">%s</div>" % "".join(hub_card(*x) for x in hub_jp))
write("services.html", page("配信サービス別アニメランキング", body, "Netflix・Prime Video・U-NEXT・dアニメストア・ABEMA など配信サービスごとのアニメ人気ランキング", banner="services", hero=True))

# 国別（全配信サービス合計）
country_cards = []
for region, codes in REGION:
    cards = []
    for cc in codes:
        rows = [r for r in jw if r["country"] == cc and r["service_id"] == "ALL"]
        if not rows: continue
        items = jw_items(rows, 30)
        cname = COUNTRY_JA.get(cc, cc)
        body = ("<h1>%sで人気のアニメ TOP%d（全配信サービス合計）</h1><p class=\"lead\">%sの配信サービス全体で、いま人気のアニメ（JustWatch 集計、%s）。</p>%s" % (
            esc(cname), len(items), esc(cname), esc(snap), rank_list(items, label="%s（全配信合計）" % cname, href="country/%s.html" % cc.lower())))
        write("country/%s.html" % cc.lower(), page("%sで人気のアニメランキング" % cname, body, "%sの配信サービス全体で人気のアニメTOP%d" % (cname, len(items)), 1, banner="country"))
        lis = "".join('<li><span class="rk">%d</span>%s<span class="nm">%s</span></li>' % (i["rank"], img(i.get("img"), i["title"], "cvs"), esc(i["title"])) for i in items[:3])
        cards.append('<a class="svc svc-link" href="country/%s.html"><h3>%s</h3><ol>%s</ol><span class="more">TOP30を見る →</span></a>' % (cc.lower(), esc(cname), lis))
    country_cards.append("<h2>%s</h2><div class=\"svcgrid\">%s</div>" % (region, "".join(cards)))
body = ("<h1>国別アニメランキング（全配信サービス合計）</h1><p class=\"lead\">世界27か国で、それぞれの国の配信サービス全体を合わせたアニメ人気ランキング（集計日 %s）。</p>" % esc(snap)) + "".join(country_cards)
write("country.html", page("国別アニメランキング", body, "世界27か国の配信サービス全体で人気のアニメランキング", banner="country", hero=True))

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
    write(fn, page("%s アニメ おすすめランキング" % name, b, "%sジャンルのおすすめアニメTOP30" % name, 1, banner="genre"))
write("genre.html", page("ジャンル別おすすめアニメ", "<h1>ジャンル別おすすめアニメ</h1><ul class=\"links\">%s</ul>" % "".join(links), banner="genre", hero=True))

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
    write(fn, page("%d年のおすすめアニメ" % y, b, "%d年に放送されたアニメのおすすめランキングTOP%d" % (y, len(rows)), 1, banner="year"))
ydiv = "".join('<div class="yrow"><span class="ydec">%d年代</span><div class="ylinks">%s</div></div>' % (d, "".join(v))
               for d, v in sorted(year_links.items(), reverse=True))
write("year.html", page("年別おすすめアニメ", "<h1>年別おすすめアニメ</h1><p class=\"lead\">1970年から今年まで、その年に放送・公開されたアニメを世界評価順に紹介します。</p>%s" % ydiv,
                        "1970年から今年まで、年ごとのおすすめアニメランキング", banner="year", hero=True))

def mini(items, href, title):
    lis = "".join('<li><span class="rk">%s</span>%s<span class="nm">%s%s</span></li>' % (esc(i["rank"]), img(i.get("img"), i["title"], "cvs"), tlink(i["title"]), i.get("chg", "")) for i in items[:5])
    return '<section class="card"><h2><a href="%s">%s</a></h2><ol>%s</ol><a class="more" href="%s">続きを見る →</a></section>' % (href, esc(title), lis, href)

# ---------- 今季アニメ特集 ----------
COUR = {1: "冬", 2: "冬", 3: "冬", 4: "春", 5: "春", 6: "春", 7: "夏", 8: "夏", 9: "夏", 10: "秋", 11: "秋", 12: "秋"}
_t = datetime.date.today()
SEASON_Y, SEASON_C = _t.year, COUR[_t.month]
def season_rows(y, c):
    rows = [r for r in seasonal if r["year"] == str(y) and r["cour"] == c and not is_adult(r)]
    return sorted(rows, key=lambda r: int(r["rank_popularity"] or 999))
cur_rows = season_rows(SEASON_Y, SEASON_C)
if not cur_rows:   # データがまだ無ければ一番新しいクール
    last = seasonal[-1]; SEASON_Y, SEASON_C = int(last["year"]), last["cour"]; cur_rows = season_rows(SEASON_Y, SEASON_C)
flm_set = {norm(strip_extra(r["title"])) for r in flm}
def season_items(rows, n=30, hot_flag=True):
    out = []
    for r in rows[:n]:
        t = jp_title(r)
        sub = ["%s" % (r.get("format") or "")]
        if r.get("studio"): sub.append(r["studio"])
        if r.get("average_score"): sub.append("評価 %s点" % r["average_score"])
        hot = hot_flag and norm(strip_extra(t)) in flm_set
        out.append({"rank": len(out) + 1, "title": t, "sub": " / ".join(x for x in sub if x) + (" / Filmarks で話題" if hot else ""),
                    "meta": genres_ja(r.get("genres")), "img": cover(t, r.get("anilist_id")),
                    "alts": (r.get("title_romaji"), r.get("title_english"))})
    return out
season_label = "%d年%sアニメ" % (SEASON_Y, SEASON_C)
COUR_EN = {"冬": "winter", "春": "spring", "夏": "summer", "秋": "fall"}
COUR_ORDER = ["冬", "春", "夏", "秋"]
ARCHIVE_FROM = (1970, "冬")   # データのある全シーズンの保存ページを作る（2026-10-13 ユーザー指定でまとめページを追加）
def season_slug(y, c): return "%d-%s" % (y, COUR_EN[c])
def seasons_since(start, end):
    y, c = start; out = []
    while (y, COUR_ORDER.index(c)) <= (end[0], COUR_ORDER.index(end[1])):
        out.append((y, c))
        i = COUR_ORDER.index(c) + 1
        if i == 4: y, i = y + 1, 0
        c = COUR_ORDER[i]
    return out
ARCHIVE = [sc for sc in seasons_since(ARCHIVE_FROM, (SEASON_Y, SEASON_C)) if season_rows(*sc)]
_pc = {"冬": ("秋", -1), "春": ("冬", 0), "夏": ("春", 0), "秋": ("夏", 0)}[SEASON_C]
PREV_Y, PREV_C = SEASON_Y + _pc[1], _pc[0]
prev_label = "%d年%sアニメ" % (PREV_Y, PREV_C)

def season_body(y, c, kind):
    """kind: current（今季）/ prev（前季）/ archive（それより前）"""
    rows = season_rows(y, c)
    lab = "%d年%sアニメ" % (y, c)
    lead = {"current": "今期（%d年%sクール）に放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べました。「Filmarks で話題」は国内のレビューサイトでも話題になっている作品です。" % (y, c),
            "prev": "前期（%d年%sクール）に放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べました。見逃した作品を配信でまとめて観るのにおすすめです。" % (y, c),
            "archive": "%d年%sクールに放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べた記録です。" % (y, c)}[kind]
    # 個別ページを作るのは今季・前季の作品だけ（過去の全シーズン分は数が多すぎるため）
    label = lab if kind in ("current", "prev") else None
    href = {"current": "season.html", "prev": "prev-season.html"}.get(kind)
    return "<h1>%s 人気ランキング TOP30</h1><p class=\"lead\">%s</p>%s" % (esc(lab), lead,
           rank_list(season_items(rows, hot_flag=(kind == "current")), label=label, href=href))

def nav_cards(rel):
    return ('<div class="snav"><a class="snav-c" href="%sseason.html"><span>今季</span>%s</a><a class="snav-c" href="%sprev-season.html"><span>前季</span>%s</a>'
            '<a class="snav-c" href="%sseasons.html"><span>まとめ</span>1970年からの全シーズン</a></div>' % (rel, esc(season_label), rel, esc(prev_label), rel))

# 今季
write("season.html", page("%s 人気ランキング" % season_label, season_body(SEASON_Y, SEASON_C, "current") + nav_cards(""),
                          "%sの人気ランキング。今期いちばん注目されているアニメがわかる" % season_label,
                          banner="season-" + season_slug(SEASON_Y, SEASON_C), hero=True))
# 前季
if season_rows(PREV_Y, PREV_C):
    write("prev-season.html", page("%s 人気ランキング（前季）" % prev_label, season_body(PREV_Y, PREV_C, "prev") + nav_cards(""),
                                   "%s（前季）の人気ランキングTOP30。見逃したアニメをまとめてチェック" % prev_label,
                                   banner="season-" + season_slug(PREV_Y, PREV_C), hero=True))
# 季節ごとの保存ページ
for y, c in ARCHIVE:
    kind = "current" if (y, c) == (SEASON_Y, SEASON_C) else ("prev" if (y, c) == (PREV_Y, PREV_C) else "archive")
    lab = "%d年%sアニメ" % (y, c)
    i = ARCHIVE.index((y, c))
    pn = '<p class="pn">%s%s</p>' % (
        ('<a href="%s.html">← %d年%s</a>' % (season_slug(*ARCHIVE[i - 1]), ARCHIVE[i - 1][0], ARCHIVE[i - 1][1])) if i > 0 else "<span></span>",
        ('<a href="%s.html">%d年%s →</a>' % (season_slug(*ARCHIVE[i + 1]), ARCHIVE[i + 1][0], ARCHIVE[i + 1][1])) if i + 1 < len(ARCHIVE) else "")
    body = ('<p class="crumb"><a href="../seasons.html">シーズン別</a> › %d年%s</p>' % (y, c)) + pn + season_body(y, c, kind) + pn + nav_cards("../")
    write("season/%s.html" % season_slug(y, c), page("%s 人気ランキング" % lab, body, "%sの人気ランキングTOP30" % lab, 1,
                                                     banner="season-" + season_slug(y, c), hero=True))
# まとめページ
by_y = collections.OrderedDict()
for y, c in reversed(ARCHIVE):
    by_y.setdefault(y, []).append(c)
rows_html = "".join('<div class="yrow"><span class="ydec">%d年</span><div class="ylinks spl">%s</div></div>' % (
    y, "".join('<a href="season/%s.html">%s</a>' % (season_slug(y, c), c) for c in COUR_ORDER if c in cs)) for y, cs in by_y.items())
body = ("<h1>シーズン別アニメランキング</h1><p class=\"lead\">1970年から今期まで、クール（冬・春・夏・秋）ごとに放送が始まったアニメの人気ランキングをまとめました。</p>"
        + '<div class="grid">%s%s</div>' % (mini(season_items(season_rows(SEASON_Y, SEASON_C)), "season.html", "今季：" + season_label),
                                           mini(season_items(season_rows(PREV_Y, PREV_C), hot_flag=False), "prev-season.html", "前季：" + prev_label))
        + "<h2>過去のシーズン</h2>" + rows_html)
SEASONS_BODY = body

# ---------- トップ ----------


write("seasons.html", page("シーズン別アニメランキング（1970年〜）", SEASONS_BODY, "1970年から今期まで、クールごとのアニメ人気ランキングまとめ", banner="seasons", hero=True))

SVC_ICON = {"Netflix": "nfx", "Amazon Prime Video": "amp", "Disney+": "dnp", "Crunchyroll": "cru",
            "Hulu": "hlu", "HBO Max": "mxx", "Apple TV+": "atp"}
import shutil
if os.path.isdir(os.path.join(HERE, "assets", "svc")):
    shutil.copytree(os.path.join(HERE, "assets", "svc"), os.path.join(OUT, "svc"), dirs_exist_ok=True)
if os.path.isdir(os.path.join(HERE, "assets", "banner")):   # ページごとのサムネイル
    os.makedirs(os.path.join(OUT, "banner"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "assets", "banner")):
        if f.endswith(".jpg"): shutil.copy(os.path.join(HERE, "assets", "banner", f), os.path.join(OUT, "banner", f))
if os.path.isdir(os.path.join(HERE, "assets", "root")):   # Search Console の確認ファイルなど、サイト直下に置くもの
    for f in os.listdir(os.path.join(HERE, "assets", "root")):
        shutil.copy(os.path.join(HERE, "assets", "root", f), os.path.join(OUT, f))
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
            n, img(cover(r.get("title_ja"), None, r["title"]), nm(r), "cvs"), tlink(nm(r))) for n, r in enumerate(picks, 1)))

HERO_IMG = os.path.exists(os.path.join(OUT, "thumbnail.jpg"))
body = (("""<section class="hero hero-img"><h1 class="vh">%s</h1>
<img src="thumbnail.jpg" alt="推しアニメランキング（毎月更新）｜世界27か国・国内13サービスの配信ランキングと歴代評価から「いま観るべきアニメ」がわかる" width="1200" height="630">
<p class="vh">世界27か国・国内12サービスの配信ランキングと、歴代の評価データから「いま観るべきアニメ」を毎月更新で紹介します。</p></section>""" if HERO_IMG else
"""<section class="hero"><h1>%s</h1>
<p>世界27か国・国内12サービスの配信ランキングと、歴代の評価データから「いま観るべきアニメ」を毎月更新で紹介します。</p></section>""") + """
<div class="grid">%s%s%s%s%s%s</div>
<h2>配信サービス別 世界TOP5 <a class="h2more" href="services.html">すべてのサービス →</a></h2><div class="svcgrid">%s</div>
<h2>探す</h2><p class="find"><a href="season.html">%s 人気ランキング →</a></p><p class="find"><a href="prev-season.html">前季アニメ 人気ランキング →</a></p><p class="find"><a href="seasons.html">シーズン別ランキング（1970年〜）→</a></p><p class="find"><a href="genre.html">ジャンル別のおすすめ →</a></p><p class="find"><a href="year.html">年別のおすすめ（1970年〜）→</a></p><p class="find"><a href="services.html">配信サービス別ランキング（13サービス）→</a></p><p class="find"><a href="country.html">国別ランキング（27か国）→</a></p>
""") % (esc(CFG["site_name"]),
       mini(season_items(cur_rows), "season.html", season_label),
       mini(now_items(now_j, prev=PREV_J), "now-japan.html", "国内いま人気"),
       mini(now_items(now_w, prev=PREV_W), "now-world.html", "世界いま人気"),
       mini(nf_items(nf_g), "netflix.html", "Netflix 世界"),
       mini(anilist_items(world), "best-world.html", "歴代・世界評価"),
       mini([{"rank": r["rank"], "title": r["title"], "chg": chg_badge(r["rank"], r["title"], PREV_F)} for r in flm], "now-japan.html", "Filmarks 話題"),
       svc_cards, esc(season_label))
write("index.html", page("トップ", body, "配信ランキングと歴代評価でえらぶ、いま観るべきおすすめアニメ"))

# ---------- 作品の個別ページ ----------
def pv_block(k):
    """公式 YouTube の PV。サムネイルは YouTube 公式画像を直接表示（コピーしない）。プレーヤーはクリックまで読み込まない"""
    v = PV.get(k) or {}
    if not v.get("video_id"): return ""
    vid = esc(v["video_id"])
    return ('<h2>公式 PV（YouTube）</h2><div class="pv" data-id="%s"><button class="pv-btn" type="button" aria-label="PV を再生">'
            '<img class="pv-img" src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="" loading="lazy" referrerpolicy="no-referrer">'
            '<span class="pv-play">▶</span><span class="pv-t">%s</span></button></div>'
            '<p class="note">出典: YouTube「%s」公式チャンネル（%s 公開）。再生ボタンを押すと YouTube の動画を読み込みます。</p>'
            '<script>document.querySelectorAll(".pv").forEach(function(b){b.querySelector("button").onclick=function(){'
            'b.innerHTML=\'<iframe src="https://www.youtube-nocookie.com/embed/\'+b.dataset.id+\'?autoplay=1&rel=0" title="公式PV" '
            'allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>\';};});</script>'
            % (vid, vid, esc(v.get("video_title", "")), esc(v.get("channel", "")), esc(v.get("published", ""))))

META = {}
for r in world + read_json(os.path.join(DATA, "japan_top.json")) + seasonal:
    for k in ("title_native", "title_romaji", "title_english"):
        if r.get(k): META.setdefault(norm(r[k]), r)
def meta_for(d):
    for t in [d["title"]] + sorted(d["alts"]):
        m = META.get(norm(t)) or META.get(norm(strip_extra(t)))
        if m: return m
    return None
SVC_FROM_RANK = {"ABEMA 日本": "ABEMA", "DMM TV 日本": "DMM TV", "TVer 日本": "TVer", "バンダイチャンネル 日本": "バンダイチャンネル"}
index_out = []
for k, d in TITLE_DB.items():
    t = d["title"]; m = meta_for(d)
    year = (m.get("season_year") or m.get("year")) if m else ""
    index_out.append({"key": k, "title": t, "alts": sorted(d["alts"]), "year": year})
    info = []
    if m:
        if year: info.append(("放送・公開", "%s年" % year))
        if m.get("format"): info.append(("形式", m["format"]))
        if m.get("episodes") and m.get("format") != "MOVIE": info.append(("話数", "%s話" % m["episodes"]))
        if m.get("genres"): info.append(("ジャンル", genres_ja(m["genres"])))
        if m.get("studio"): info.append(("制作", m["studio"]))
        if m.get("average_score"): info.append(("世界評価", "%s点（AniList）" % m["average_score"]))
    kg = kakugen(t)
    w = WATCH.get(k) or {}
    extra = [v for lab, v in SVC_FROM_RANK.items() if any(a[0] == lab for a in d["apps"])]
    flat = list(dict.fromkeys((w.get("flatrate") or []) + extra))
    rent = w.get("rent_buy") or []
    free = w.get("free") or []
    watch = ""
    if flat or rent or free:
        rows_ = []
        if flat: rows_.append('<div class="wrow"><span class="wlb">見放題</span>%s</div>' % "".join('<span class="chip">%s</span>' % esc(x) for x in flat))
        if free: rows_.append('<div class="wrow"><span class="wlb">無料</span>%s</div>' % "".join('<span class="chip">%s</span>' % esc(x) for x in free))
        if rent: rows_.append('<div class="wrow"><span class="wlb">レンタル・購入</span>%s</div>' % "".join('<span class="chip">%s</span>' % esc(x) for x in rent))
        series_note = ("「%s」シリーズ全体の配信状況です。この作品（続編・劇場版）が含まれるかは各サービスで確認してください。" % esc(w["series"])) if w.get("series") else ""
        watch = ('<h2>どこで観られる？（日本）</h2>%s<p class="note">%sJustWatch と各サービスのランキングから集計（%s 時点）。配信状況は変わることがあるので、最新は各サービスで確認してください。</p>'
                 % ("".join(rows_), series_note, esc(w.get("date") or snap)))
    else:
        watch = '<h2>どこで観られる？（日本）</h2><p class="note">日本の配信状況はまだ確認できていません。</p>'
    apps = "".join('<tr><td><a href="../%s">%s</a></td><td class="r">%s位</td><td class="s">%s</td></tr>' % (esc(h), esc(lab), esc(rk), esc(sb))
                   for lab, rk, h, sb in sorted(d["apps"], key=lambda a: int(a[1]) if str(a[1]).isdigit() else 99))
    body = ('<p class="crumb"><a href="../index.html">トップ</a> › 作品</p><h1 class="wt">%s</h1>' % esc(t) +
            ((('<blockquote class="kgq orig"><span class="kgl">ひとこと格言（当サイトオリジナル・作中のセリフではありません）</span>%s</blockquote>' % esc(kg["q"]))
              if kg.get("original") else
              ('<blockquote class="kgq"><span class="kgl">作中の名言</span>「%s」<span class="kgw">— %s『%s』より</span></blockquote>' % (esc(kg["q"]), esc(kg["who"]), esc(t)))) if kg else "") +
            (('<table class="info">%s</table>' % "".join('<tr><th>%s</th><td>%s</td></tr>' % (esc(a), esc(b)) for a, b in info)) if info else "") +
            pv_block(k) + watch +
            '<h2>ランキングでの順位</h2><table class="apps">%s</table>' % apps +
            '<h2>Blu-ray・原作・グッズ</h2>' + shop_buttons(t))
    desc = "%sはどこで観られる？配信サービス・ランキング順位・%sまとめ" % (t, "名言・" if kg else "")
    write("anime/%s.html" % k, page("%sはどこで観られる？配信・ランキングまとめ" % t, body, desc, 1))
json.dump(index_out, open(os.path.join(HERE, "titles_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 固定ページ ----------
write("about.html", page("このサイトについて", """<h1>このサイトについて</h1>
<p>「%s」は、世界と日本の配信ランキング・レビューサイトの評価データを毎月集計し、おすすめアニメを紹介する個人運営サイトです。</p>
<h2>データの出典</h2>
<ul><li>AniList（世界最大級のアニメデータベース）: 歴代評価・ジャンル・年別</li>
<li>Netflix Tudum 公式 Top 10: 週間ランキング・再生回数</li>
<li>JustWatch: 各国・各配信サービスの人気ランキング</li>
<li>ABEMA・DMM TV・TVer・バンダイチャンネル: 各サービスのランキング画面</li>
<li>Filmarks: 話題のアニメ・5段階評価</li></ul>
<p>配信サービスのアイコンは JustWatch より。</p>
<h2>運営者</h2><p>Masabee（YouTube: <a href="https://www.youtube.com/@Masabee1029" target="_blank" rel="noopener">@Masabee1029</a>）</p>
<h2>お問い合わせ</h2><p>%s</p>
<h2>広告について</h2><p>当サイトは Amazon.co.jp アソシエイト、楽天アフィリエイト、もしもアフィリエイト（Yahoo!ショッピング等）のアフィリエイトプログラムに参加しています。リンク先での購入・契約により当サイトに紹介料が支払われることがありますが、ランキングの順位は収益によって変わりません。</p>
""" % (esc(CFG["site_name"]), ('<a href="%s">お問い合わせフォーム</a>' % esc(CFG["contact_url"])) if CFG.get("contact_url") else "準備中（YouTube チャンネルのコメント欄からご連絡ください）")))

GA_POLICY = ("""<p>当サイトでは、サイトの利用状況を把握するために、Google LLC が提供するアクセス解析ツール「Google アナリティクス」を利用しています。Google アナリティクスは Cookie を使って、閲覧したページ、滞在時間、おおよその地域、利用端末やブラウザの種類などの情報を収集し、Google LLC に送信します。これらの情報は個人を特定するものではありません。</p>
<p>収集されたデータは Google のプライバシーポリシーに基づいて管理されます。詳しくは「<a href="https://policies.google.com/technologies/partner-sites?hl=ja" target="_blank" rel="noopener">Google のサービスを使用するサイトやアプリから収集した情報の Google による使用</a>」をご覧ください。データの収集を望まない場合は、ブラウザの Cookie を無効にするか、<a href="https://tools.google.com/dlpage/gaoptout?hl=ja" target="_blank" rel="noopener">Google アナリティクス オプトアウト アドオン</a>を利用することで停止できます。</p>"""
             if GA_TAG else
             "<p>当サイトでは、今後 Google アナリティクス等のアクセス解析ツールを利用する場合があります。これらはトラフィックデータ収集のために Cookie を使用しますが、個人を特定するものではありません。</p>")
write("privacy.html", page("プライバシーポリシー", """<h1>プライバシーポリシー</h1>
<h2>広告の配信について</h2>
<p>当サイトは、Amazon.co.jp を宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。また楽天アフィリエイト、もしもアフィリエイトを利用しています。</p>
<h2>アクセス解析について</h2>
%s
<h2>免責事項</h2>
<p>当サイトの情報は、できる限り正確な情報を掲載するよう努めていますが、ランキングは外部データの集計であり、正確性・最新性を保証するものではありません。リンク先の商品・サービスについては各提供元にお問い合わせください。</p>
<p>制定日: 2026年10月11日%s</p>""" % (GA_POLICY, "／改定日: 2026年10月13日" if GA_TAG else "")))

# ---------- CSS ----------
write("style.css", """
:root{--bg:#0f1115;--card:#171a21;--tx:#e8e8ea;--mu:#9aa0ab;--ac:#ff6b9d;--line:#262a33}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.8}
a{color:var(--ac)}header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 24px;padding:16px 20px;border-bottom:1px solid var(--line);background:var(--card)}
.logo{font-weight:800;font-size:1.75rem;letter-spacing:.02em;line-height:1.3;text-decoration:none;color:var(--tx)}.logo b{color:var(--ac)}nav{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.9rem}nav a{text-decoration:none;color:var(--mu)}nav a:hover{color:var(--ac)}
.pr{font-size:.75rem;color:var(--mu);margin:6px auto 0;max-width:1180px;padding:0 16px}
.layout{max-width:1180px;margin:0 auto;padding:8px 16px 40px;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:32px;align-items:start}
@media(max-width:1023px){.layout{grid-template-columns:minmax(0,1fr)}}main{min-width:0}
.side{display:flex;flex-direction:column;gap:16px;padding-top:16px}.sbox{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-size:.88rem}
.sbox.sticky{position:sticky;top:12px}.sh{font-weight:800;margin-bottom:8px;border-left:4px solid var(--ac);padding-left:8px}.prc{font-size:.65rem;font-weight:700;border:1px solid var(--mu);color:var(--mu);border-radius:4px;padding:0 4px;margin-left:4px;vertical-align:middle}
.slist{list-style:none;margin:0;padding:0}.slist li{border-top:1px solid var(--line)}.slist a{display:block;padding:7px 2px;text-decoration:none;color:var(--tx)}.slist a:hover{color:var(--ac)}
.prof{display:flex;gap:10px;align-items:flex-start}.prof p{margin:0;font-size:.82rem;color:var(--mu);line-height:1.7}
.avatar{flex:0 0 48px;width:48px;height:48px;border-radius:50%;background:var(--ac);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.2rem}
.sbtn{--bc:#ff6b9d;display:block;text-align:center;margin:8px 0 0;padding:10px;border-radius:10px;background:var(--bc);color:#fff;text-decoration:none;font-weight:800}
.author{display:flex;gap:14px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:24px 0}.author p{margin:4px 0 0;font-size:.85rem;color:var(--mu)}
.share{display:flex;gap:8px;flex-wrap:wrap;margin:32px 0 8px}.share a{flex:1 1 90px;text-align:center;padding:8px;border-radius:8px;color:#fff;text-decoration:none;font-size:.8rem;font-weight:700}
.share .sx{background:#000;border:1px solid #444}.share .sl{background:#06c755}.share .sb{background:#00a4de}
@media(max-width:640px){nav{flex-wrap:nowrap;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch;padding-bottom:4px}}
h1{font-size:1.5rem;margin:16px 0 8px}h2{font-size:1.2rem;margin:40px 0 12px;border-left:4px solid var(--ac);padding-left:8px}.lead{color:var(--mu);font-size:.95rem;margin:0 0 20px}
ol.rank{list-style:none;padding:0;margin:0}ol.rank li{display:flex;gap:16px;padding:20px 0;border-bottom:1px solid var(--line)}
.rk{flex:0 0 2.2em;font-size:1.4rem;font-weight:800;color:var(--ac);text-align:right}ol.rank li:nth-child(-n+3) .rk{color:#ffd166}
.cv{flex:0 0 72px;width:72px;height:102px;object-fit:cover;border-radius:6px;background:#222}.noimg{background:linear-gradient(135deg,#262a33,#1a1d24)}
.tile{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;text-shadow:0 1px 3px rgba(0,0,0,.35)}.cv.tile span{font-size:2rem}.cvs.tile{display:inline-flex}.cvs.tile span{font-size:.85rem}
.cvs{display:inline-block;width:28px;height:40px;object-fit:cover;border-radius:3px;vertical-align:middle;margin-right:6px;background:#222}
.body{flex:1;min-width:0}.tt{font-weight:700;font-size:1.05rem;line-height:1.5;margin-bottom:4px}.sub,.meta{font-size:.82rem;color:var(--mu);line-height:1.7}
.shop{margin-top:12px}.shop-lb{display:block;font-size:.72rem;color:var(--mu);margin-bottom:4px;letter-spacing:.02em}
.shop-btns{display:flex;flex-wrap:wrap;gap:8px}
.btn{--bc:#888;font-size:.75rem;padding:3px 12px;border-radius:999px;text-decoration:none;background:#000;color:var(--bc);border:1px solid var(--bc);transition:background .15s}
.btn:hover{background:#1a1a1a}
.btn.amz{--bc:#ff9900}.btn.rkt{--bc:#ff4d4d}.btn.yho{--bc:#ff4d6d}
.hero{padding:24px 0 8px}.hero h1{font-size:1.8rem}.hero-img{padding:20px 0 12px}.hero-img img{display:block;width:100%;height:auto;border-radius:14px;border:1px solid var(--line)}
.page-hero{margin:16px 0 4px}.page-hero img{display:block;width:100%;height:auto;border-radius:14px;border:1px solid var(--line)}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}@media(max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px}.card h2{margin:0 0 8px;font-size:1.05rem;border:0;padding:0}.card h2 a{text-decoration:none}
.card ol{list-style:none;padding:0;margin:0}.card li{padding:6px 0;font-size:.92rem;line-height:1.5;display:flex;align-items:center;gap:2px}.nm{flex:1;min-width:0;overflow-wrap:anywhere}.card .rk{display:inline-block;width:1.6em;font-size:1rem;margin-right:4px;flex:0 0 auto}.cvs{flex:0 0 auto}
.more{display:inline-block;margin-top:8px;font-size:.85rem}.svcgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.svc{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-size:.88rem}
.svc h3{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:1rem}.svc-ic{width:28px;height:28px;border-radius:7px}.svc ol{list-style:none;margin:0;padding:0}.svc li{display:flex;align-items:center;gap:2px;padding:5px 0;line-height:1.5}.svc .rk{display:inline-block;width:1.6em;font-size:.95rem;margin-right:4px;flex:0 0 auto}
.svc-link{display:block;text-decoration:none;color:var(--tx)}.svc-link:hover{border-color:var(--ac)}.svc-ic.txt{display:inline-flex;align-items:center;justify-content:center;background:#333;color:#fff;font-size:.8rem}.h2more{font-size:.8rem;font-weight:400;margin-left:8px}
.snav{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:28px 0 8px}@media(max-width:640px){.snav{grid-template-columns:1fr}}
.snav-c{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-decoration:none;color:var(--tx);font-weight:700}.snav-c:hover{border-color:var(--ac)}.snav-c span{display:block;font-size:.72rem;font-weight:400;color:var(--ac)}
.spl a{display:inline-block;min-width:3.2em;text-align:center;padding:4px 12px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-weight:700}.spl a:hover{border-color:var(--ac)}
.find{margin:6px 0}.find a{font-size:1rem}.pn{display:flex;justify-content:space-between;font-size:.9rem;margin:12px 0}
.yrow{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid var(--line);align-items:baseline}.ydec{flex:0 0 5em;font-weight:700;color:var(--mu)}.ylinks{display:flex;flex-wrap:wrap;gap:6px 14px}
footer{border-top:1px solid var(--line);padding:16px;font-size:.78rem;color:var(--mu);text-align:center}
a.tl{color:var(--tx);text-decoration:none;border-bottom:1px dotted #555}a.tl:hover{color:var(--ac)}
.chg{display:block;font-size:.65rem;font-weight:700;line-height:1.2;margin-top:2px}.card .chg,.svc .chg{display:inline;margin-left:6px}.chg.up{color:#5fd38d}.chg.dn{color:#8a8f99}.chg.eq{color:#8a8f99}.chg.new{color:#ffd166}
.kg.orig{color:#e6dcc8;border-left-color:#c9a86a}.kgq.orig{border-left-color:#c9a86a}
.kg{font-size:.85rem;color:#ffd9e6;margin:4px 0 2px;padding-left:10px;border-left:2px solid var(--ac)}
.watch{font-size:.8rem;color:#bfe6cf;margin-top:4px}
.crumb{font-size:.8rem;color:var(--mu);margin:12px 0 0}.wt{font-size:1.7rem;line-height:1.4}
.kgw{display:block;font-size:.75rem;font-weight:400;color:var(--mu);margin-top:2px}.kg .kgw{display:inline;margin-left:6px}
.kgq{margin:16px 0 24px;padding:16px 20px;background:var(--card);border-left:4px solid var(--ac);border-radius:8px;font-size:1.15rem;font-weight:700}.kgl{display:block;font-size:.72rem;font-weight:400;color:var(--mu);margin-bottom:4px}
.info{border-collapse:collapse;width:100%;font-size:.9rem}.info th{text-align:left;color:var(--mu);font-weight:400;width:7em;padding:6px 0;vertical-align:top}.info td{padding:6px 0}.info tr{border-bottom:1px solid var(--line)}
.wrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0}.wlb{flex:0 0 8em;font-size:.8rem;color:var(--mu)}.chip{font-size:.82rem;padding:3px 12px;border-radius:999px;border:1px solid #3a8f63;color:#bfe6cf}
.note{font-size:.75rem;color:var(--mu)}
.pv{position:relative;width:100%;aspect-ratio:16/9;background:linear-gradient(140deg,#2a1830,#101420);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.pv iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.pv-btn{all:unset;cursor:pointer;position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:#fff;text-align:center;padding:16px}
.pv-play{width:72px;height:72px;border-radius:50%;border:2px solid var(--ac);display:flex;align-items:center;justify-content:center;font-size:1.6rem;color:var(--ac)}
.pv-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}.pv-btn::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15),rgba(0,0,0,.6));z-index:0}.pv-play,.pv-t{position:relative;z-index:1}.pv-play{background:rgba(0,0,0,.45)}.pv-btn:hover .pv-play{background:var(--ac);color:#fff}.pv-t{font-size:.9rem;color:#fff;max-width:90%;text-shadow:0 1px 4px #000}
.apps{border-collapse:collapse;width:100%;font-size:.9rem}.apps td{padding:7px 4px;border-bottom:1px solid var(--line)}.apps .r{font-weight:700;color:var(--ac);white-space:nowrap}.apps .s{color:var(--mu);font-size:.8rem}
""")
# GitHub Pages 用
write(".nojekyll", "")
# ---------- サイトマップ・robots ----------
base = CFG["site_url"].rstrip("/") + "/"
urls = [n for n in PAGES if n.endswith(".html")]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n" % (base, "" if n == "index.html" else n, TODAY) for n in urls) + "</urlset>\n")
write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n" % base)
flush()
print("generated", len([f for _, _, fs in os.walk(OUT) for f in fs]), "files in docs/")
