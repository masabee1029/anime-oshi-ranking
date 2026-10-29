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

def neowing_link(title):
    """NEOWING（CD・Blu-ray・アニメグッズ）。バリューコマースのリンクに作品名の検索ページを vc_url で付ける（affiliate.json の neowing_vc: {sid, pid}。2026-10-28 追加）"""
    nv = CFG.get("neowing_vc") or {}
    if not nv.get("pid"):
        return ""
    dest = "https://www.neowing.co.jp/searchuni?q=" + urllib.parse.quote(title)
    return "https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=%s&pid=%s&vc_url=%s" % (nv["sid"], nv["pid"], urllib.parse.quote(dest, safe=""))

def shop_buttons(title):
    def a(cls, url, label, style=""):
        return '<a class="btn %s" %shref="%s" target="_blank" rel="nofollow sponsored noopener">%s</a>' % (
            cls, ('style="%s" ' % style) if style else "", esc(url), label)
    shops = [a("amz", amazon_link(title), "Amazon"), a("rkt", rakuten_link(title), "楽天")]
    if yahoo_link(title):
        shops.append(a("yho", yahoo_link(title), "Yahoo!"))
    if neowing_link(title):
        shops.append(a("neo", neowing_link(title), "NEOWING", "background:#0a7bc2;color:#fff"))
    html_ = ('<div class="shop"><span class="shop-lb">Blu-ray・原作・グッズを探す</span>'
             '<div class="shop-btns">%s</div></div>' % "".join(shops))
    vods = [a("vod", sv["url"], esc(sv["name"]), "--bc:%s" % esc(sv.get("color") or "#888"))
            for sv in CFG.get("streaming", []) if sv.get("url")]
    if vods:
        html_ += ('<div class="shop"><span class="shop-lb">配信で観る（無料体験あり）</span>'
                  '<div class="shop-btns">%s</div></div>' % "".join(vods))
    return html_

GOODS = read_json(os.path.join(HERE, "goods.json")) if os.path.exists(os.path.join(HERE, "goods.json")) else {}
def goods_pick(k, m):
    """作品ごとのおすすめグッズ 1 つ（goods.json に {key: {item, why}} があれば優先。無ければ形式・ジャンル・年から選ぶ）"""
    if GOODS.get(k): return GOODS[k]["item"], GOODS[k]["why"]
    m = m or {}; g = set((m.get("genres") or "").split("|"))
    y = m.get("season_year") or m.get("year") or 0
    try: y = int(y)
    except Exception: y = 0
    if m.get("format") == "MOVIE":
        return "パンフレット", "劇場で売られた公式パンフレットは、スタッフ・キャストのインタビューや設定資料が読める映画ファンの定番グッズです。"
    if "Sports" in g:
        return "マフラータオル", "スポーツ作品は応援グッズが似合います。マフラータオルなら観戦気分で飾ったり使ったりできます。"
    if "Music" in g:
        return "サウンドトラック", "音楽が主役の作品なので、劇中の曲をまとめたサウンドトラック（CD・配信）で名場面をもう一度楽しめます。"
    if "Mecha" in g:
        return "プラモデル", "ロボット作品なら、劇中の機体を自分の手で組み立てられるプラモデルがいちばんの楽しみです。"
    if y and y < 2005:
        return "設定資料集", "放送から年月がたった名作は、キャラクターや世界観の設定画をまとめた資料集で制作の裏側を楽しめます。"
    return "アクリルスタンド", "推しキャラを机や棚に飾れるアクリルスタンドは、手ごろな価格で集めやすい定番グッズです。"

def goods_block(t, item, why):
    q = "%s %s" % (t, item)
    def a(cls, url, label):
        return '<a class="btn %s" href="%s" target="_blank" rel="nofollow sponsored noopener">%s</a>' % (cls, esc(url), label)
    shops = [a("amz", amazon_link(q), "Amazon"), a("rkt", rakuten_link(q), "楽天")]
    if yahoo_link(q): shops.append(a("yho", yahoo_link(q), "Yahoo!"))
    return ('<h2>おすすめのグッズ</h2><div class="goods"><p class="goods-n">%s</p><p class="goods-w">%s</p></div>'
            '<div class="shop"><span class="shop-lb">「%s」を探す</span><div class="shop-btns">%s</div></div>'
            % (esc(q), esc(why), esc(q), "".join(shops)))

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
PROFILE = ("見に来てくださって、ありがとうございます。あなたが「次に観る1本」を迷わず選べるように、Netflix 公式 Top10・JustWatch・AniList・Filmarks のデータを"
           "毎月集計してランキングにまとめています。運営者もアニメ好きで、歌い手やボカロなど音楽の推し活もしています。")

def sidebar(rel):
    rank = "".join('<li><a href="%s%s">%s</a></li>' % (rel, h, t) for h, t in NAV[1:])
    svc = "".join('<a class="sbtn" rel="nofollow sponsored noopener" target="_blank" href="%s" style="--bc:%s">%s</a>'
                  % (esc(x["url"]), esc(x.get("color", "#ff6b9d")), esc(x["name"])) for x in CFG.get("streaming", []) if x.get("url"))
    sis = "".join('<li><a href="https://masabee1029.github.io/%s/" target="_blank" rel="noopener">%s</a></li>' % (p, esc(n)) for n, p in SISTER_SITES)
    return ('<aside class="side">'
            '<div class="sbox"><div class="sh">運営者</div><div class="prof"><div class="avatar">推</div><p>%s</p></div>'
            '<a class="more" href="%sabout.html">このサイトについて</a></div>'
            '%s%s'
            '<div class="sbox"><div class="sh">ランキング一覧</div><ul class="slist">%s</ul></div>'
            '<div class="sbox"><div class="sh">姉妹サイト</div><ul class="slist">%s</ul></div>'
            '</aside>') % (esc(PROFILE), rel,
                           ('<div class="sbox sticky"><div class="sh">アニメを観るなら <span class="prc">PR</span></div>%s'
                            '<p class="note">配信作品・料金・無料期間の最新は、各サービスの公式サイトでご確認いただけます。</p></div>' % svc) if svc else "",
                           vc_box(), rank, sis)

# バリューコマースの提携広告（affiliate.json の vc_ads。審査中は vc_ads_pending に置いて出さない。2026-10-25 追加）
def vc_box():
    ads = [a for a in CFG.get("vc_ads", []) if a.get("url")]
    if not ads:
        return ""
    items = "".join('<div class="vcad"><strong>%s</strong><span>%s</span>'
                    '<a class="sbtn" rel="nofollow sponsored noopener" target="_blank" href="%s" style="--bc:#3fc1a5">%s</a>%s</div>'
                    % (esc(a["name"]), esc(a.get("note", "")), esc(a["url"]), esc(a.get("btn", "公式サイトを見る")),
                       '<img src="%s" height="1" width="1" alt="" style="border:0">' % esc(a["beacon"]) if a.get("beacon") else "")
                    for a in ads)
    return '<div class="sbox"><div class="sh">グッズ・音楽を探すなら <span class="prc">PR</span></div>%s</div>' % items

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
    if "data-anim" in body: body += ANIM_JS
    if '<ol class="rank">' in body: body += RANK_JS
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

ANIM_JS = ("<script>(function(){var rm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;"
           "document.querySelectorAll('[data-anim]').forEach(function(s){if(rm)return;var a=s.querySelectorAll('animate');"
           "a.forEach(function(x){x.parentNode.setAttribute('width',0)});s.classList.add('wait');"
           "var b=function(){a.forEach(function(x){try{x.beginElement()}catch(e){x.parentNode.setAttribute('width',x.getAttribute('to'))}})};"
           "var go=function(){s.classList.add('go');if(document.readyState==='complete')setTimeout(b,30);else addEventListener('load',function(){setTimeout(b,30)})};"
           "if(!('IntersectionObserver' in window))return go();var o=new IntersectionObserver(function(e){if(e[0].isIntersecting){go();o.disconnect()}},{threshold:.3});o.observe(s)})})()</script>")
RANK_JS = ("<script>(function(){if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;"
           "var L=document.querySelectorAll('ol.rank>li');if(!L.length||!('IntersectionObserver' in window))return;"
           "var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');o.unobserve(e.target)}})},{threshold:.15,rootMargin:'0px 0px -8% 0px'});"
           "L.forEach(function(li){li.classList.add('rv');o.observe(li)})})()</script>")
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
import unicodedata
_CANON, ALIAS = {}, {}   # 全角・半角だけ違う同じ作品（Season２ と Season2 など）を 1 ページにまとめる（2026-10-29）
def tkey(title):
    t = FIX_TITLE.get(title, title)
    h = hashlib.md5(norm(t).encode("utf-8")).hexdigest()[:10]
    k = _CANON.setdefault(norm(unicodedata.normalize("NFKC", t or "")), h)
    if k != h: ALIAS[h] = k
    return k
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

SCORE_RE = re.compile(r"評価 ([0-9.]+)(点| / 5\.0)")
def score_badge(sub):
    """サブ行の「評価 85点」「評価 4.3 / 5.0」を取り出して、大きな数字＋メーターにする（2026-10-29 ユーザー「評価点をもっと大きく」）"""
    m_ = SCORE_RE.search(sub or "")
    if not m_: return "", sub
    v, five = float(m_.group(1)), m_.group(2) != "点"
    pct = v / 5.0 * 100 if five else v
    rest = " / ".join(x for x in SCORE_RE.sub("", sub).split(" / ") if x.strip())
    num = ("%.1f" % v) if five else ("%d" % round(v))
    return ('<div class="sc"><span class="sc-l">%s</span><b class="sc-n">%s</b><span class="sc-u">%s</span>'
            '<span class="sc-m"><i style="width:%.0f%%"></i></span></div>'
            % ("みんなの評価" if five else "世界評価", num, "/ 5.0" if five else "点 / 100", pct)), rest
def rank_list(items, show_shop=True, label=None, href=None):
    """items: list of dict(rank,title,sub,meta,chg)。label を渡すと作品の個別ページに記録する"""
    rows = []
    for it in items:
        if label:
            register(it["title"], label, it["rank"], href, it.get("sub", ""), it.get("alts", ()))
        kg = kakugen(it["title"])
        badge, sub_ = score_badge(it.get("sub", ""))
        rows.append('<li><span class="rk">%s%s</span>%s<div class="body"><div class="tt">%s</div>'
                    '%s<div class="sub">%s</div>%s%s%s%s</div></li>' % (
                        esc(it["rank"]), it.get("chg", ""), img(it.get("img"), it["title"]), tlink(it["title"]), badge, esc(sub_),
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

# ---------- グラフの部品（2026-10-29 全ページにグラフ） ----------
YEAR_OF = {}
for r_ in seasonal + world:
    y_ = r_.get("season_year") or r_.get("year")
    if not (y_ and str(y_).isdigit()): continue
    for k_ in ("title_native", "title_romaji", "title_english"):
        if r_.get(k_): YEAR_OF.setdefault(norm(r_[k_]), int(y_))
def year_of(*names):
    for t in names:
        if t and norm(t) in YEAR_OF: return YEAR_OF[norm(t)]
        if t and norm(strip_extra(t)) in YEAR_OF: return YEAR_OF[norm(strip_extra(t))]
    return None

def bar_chart(h2, rows, note, more="", ranked=True, mx=None):
    """横棒グラフ。rows: [(名前のHTML, 値, 右に出す文字, 名前の後ろに付けるHTML)]。画面に入ったら左から伸びる"""
    rows = [r for r in rows if r[1] and r[1] > 0]
    if len(rows) < 2: return ""
    mx = mx or max(r[1] for r in rows)
    lis = "".join('<li>%s<div class="tr-main"><div class="tr-nm">%s%s</div>'
                  '<div class="tr-row"><div class="tr-bar"><span style="width:%.1f%%;animation-delay:%.2fs"></span></div><em>%s</em></div></div></li>'
                  % (('<span class="tr-rk">%d</span>' % i) if ranked else "", nm, ex, 100.0 * v / mx, 0.06 * (i - 1), esc(lb))
                  for i, (nm, v, lb, ex) in enumerate(rows, 1))
    return ('<section class="trend" data-anim><h2>%s%s</h2><ol class="tr-list%s">%s</ol><p class="note">%s</p></section>'
            % (h2, more, "" if ranked else " nr", lis, note))

def decade_chart(h2, years, note):
    """作品の放送・公開年を 10 年ごとに数える"""
    c = collections.Counter((y // 10) * 10 for y in years if y)
    if len(c) < 2: return ""
    return bar_chart(h2, [("%d年代" % d, n, "%d作品" % n, "") for d, n in sorted(c.items(), reverse=True)], note, ranked=False)

def genre_chart(h2, genre_strs, note, n=8):
    c = collections.Counter(GENRE_JA.get(g, g) for gs in genre_strs for g in (gs or "").split("|") if g and GENRE_JA.get(g, g))
    if len(c) < 2: return ""
    return bar_chart(h2, [(esc(g), k, "%d作品" % k, "") for g, k in c.most_common(n)], note, ranked=False)

def trend_chart(rows, prev, n=10, h2="今月の人気の動き（世界TOP10）", more=' <a class="h2more" href="now-world.html">TOP30を見る →</a>'):
    """世界27か国の点数（各国1位=30点…30位=1点の合計）の横棒と、先月からの順位の動き"""
    items = []
    for r in rows:
        if len(items) >= n: break
        t = r["title"] if (r.get("original_title") and r.get("title")) else (r.get("title_ja") or r.get("title"))
        if t in EXCLUDE or r.get("title") in EXCLUDE or r.get("title_ja") in EXCLUDE: continue
        try: pts = int(float(r.get("points") or 0))
        except ValueError: pts = 0
        if pts <= 0: continue
        items.append((tlink(FIX_TITLE.get(t, t)), pts, "%d点・%sか国" % (pts, r.get("countries_in_top30") or ""), chg_badge(len(items) + 1, r["title"], prev)))
    note = ("棒の長さは、世界27か国の配信ランキングで各国1位=30点〜30位=1点として合計した人気の大きさです。"
            + ("矢印は先月からの順位の動きです。" if prev is not None else "先月からの順位の動き（↑↓）は、次の集計から表示します。"))
    return bar_chart(h2, items, "%s（%s 集計）" % (note, esc(snap)), more)

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
<p class="lead">いま日本で観られているアニメが、ひと目でわかります。Netflix・Prime Video・U-NEXT・dアニメストア・Disney+・Hulu などの国内ランキングを合算しました（集計日 %s、毎月更新）。</p>
%s%s
<h2>Filmarks で話題のアニメ</h2>
<p class="lead">観た人の声で選びたいあなたに。レビューサイト Filmarks の「話題のアニメ」です。数字は5点満点の平均評価。</p>
%s""" % (esc(snap), decade_chart("いま人気の30本は、いつの作品？", [int(r["year"]) if (r.get("year") or "").isdigit() else year_of(r.get("title"), r.get("original_title")) for r in now_j if r.get("title") not in EXCLUDE][:30],
                                     "国内いま人気 TOP30 の作品を、放送・公開された年代ごとに数えました。新作だけでなく、昔の名作も観られています。"),
         rank_list(now_items(now_j, prev=PREV_J), label="国内いま人気（全配信合算）", href="now-japan.html"),
         rank_list([{"rank": r["rank"], "title": r["title"], "sub": "評価 %s / 5.0" % r["score_5"], "img": cover(r["title"]),
                     "chg": chg_badge(r["rank"], r["title"], PREV_F)} for r in flm[:20]], label="Filmarks 話題のアニメ", href="now-japan.html"))
write("now-japan.html", page("国内いま人気のアニメ TOP30", body, "日本の配信サービス全体で今月人気のアニメランキング", banner="now-japan", hero=True))

body = """<h1>世界いま人気のアニメ TOP30（27か国・全配信合算）</h1>
<p class="lead">世界のファンがいま夢中な作品が、ひと目でわかります。世界27か国の Netflix・Prime Video・Disney+・Crunchyroll・Hulu・HBO Max・Apple TV+ のランキングを合算しました（集計日 %s）。</p>
%s%s""" % (esc(snap), trend_chart(now_w, PREV_W, h2="人気の大きさ（TOP10）", more=""), rank_list(now_items(now_w, prev=PREV_W), label="世界いま人気（27か国合算）", href="now-world.html"))
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
<p class="lead">長く愛される名作から、あなたの次の1本を選べます。世界最大級のアニメデータベース AniList の平均スコア順で、海外ファンからの評価の高さを示します。</p>
%s%s""" % (decade_chart("名作TOP100は、いつの作品？", [int(r["season_year"]) if str(r.get("season_year") or "").isdigit() else None for r in world[:100]],
                       "歴代・世界評価 TOP100 の作品を、放送・公開された年代ごとに数えました。"),
           rank_list(anilist_items(world), label="歴代・世界評価", href="best-world.html"))
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
%s%s
<h2>日本 TOP30</h2>
<p class="lead">日本で長く観られ続けている作品がわかります。日本の Netflix 週間TOP10に入った週数の多い順です。</p>
%s%s""" % (bar_chart("累計の再生回数（TOP10）", [(tlink(r.get("anime_title_ja") or r["show_title"]), int(float(r["views"] or 0)) // 10000,
                                              "%s万回" % format(int(float(r["views"] or 0)) // 10000, ","), "") for r in nf_g[:10]],
                     "Netflix 公式 Top10 に載った週の再生回数を合計した数字です。"),
           rank_list(nf_items(nf_g, prev=PREV_NG), label="Netflix 世界", href="netflix.html"),
         bar_chart("日本でTOP10に入った週の数（TOP10）", [(tlink(r.get("anime_title_ja") or r["show_title"]), int(r["weeks"] or 0), "%s週" % r["weeks"], "") for r in nf_c[:10]],
                   "日本の Netflix 週間TOP10に入った週の数です。長いほど、長く観られ続けています。"),
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

WIDE_LISTS = {}   # 年がわからないサービスは、全ランキングが揃ってから「人気の広さ」グラフを入れる
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
    body += "<h2>世界 TOP%d（27か国合算）</h2><p class=\"lead\">各国の%sアニメランキングを点数化（1位=30点…30位=1点）して合計。</p>%s%s" % (
        len(world_list), esc(name), trend_chart([r for r in rows if sid == "dnp" or r["title"] not in EXCLUDE], None, h2="%sの人気の大きさ（TOP10）" % esc(name), more="").replace("先月からの順位の動き（↑↓）は、次の集計から表示します。", ""), rank_list(world_list, label="%s 世界" % name, href="service/%s.html" % sid))
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
    body = "<h1>%s アニメランキング</h1><h2>日本 TOP%d</h2>%s%s" % (esc(name), len(jl), (lambda c_: c_ or ("\x00WIDE:%s\x00" % sid))(decade_chart("%sで人気の作品は、いつの作品？" % esc(name), [year_of(i["title"]) for i in jl],
                                                                                "%s の日本ランキングの作品を、放送・公開された年代ごとに数えました（年がわかった作品だけ）。" % esc(name))), rank_list(jl, label="%s 日本" % name, href="service/%s.html" % sid))
    write("service/%s.html" % sid, page("%s アニメランキング" % name, body, "%sで人気のアニメランキング" % name, 1, banner="services"))
    WIDE_LISTS[sid] = (name, jl)
    hub_jp.append((sid, name, jl[:3]))

HIDE_SVC_HUB = {"Apple TV+"}
def hub_card(sid, name, top):
    icon = SVC_ICON_FILE.get(sid)
    h = ('<img class="svc-ic" src="svc/%s.png" alt="" width="28" height="28">' % icon if icon else '<span class="svc-ic txt">%s</span>' % esc(name[:1])) + esc(name)
    lis = "".join('<li><span class="rk">%d</span>%s<span class="nm">%s</span></li>' % (i["rank"], img(i.get("img"), i["title"], "cvs"), esc(i["title"])) for i in top)
    return '<a class="svc svc-link" href="service/%s.html"><h3>%s</h3><ol>%s</ol><span class="more">ランキングを見る →</span></a>' % (sid, h, lis)

body = ("<h1>配信サービス別アニメランキング</h1><p class=\"lead\">あなたが使っている配信サービスで、いま人気のアニメがわかります。毎月更新（集計日 %s）。</p>" % esc(snap) +
        bar_chart("アニメがよく観られているサービス（世界）", sorted([('<a href="service/%s.html">%s</a>' % (sid, esc(nm_)), sum(int(float(r["points"] or 0)) for r in svc if r["service"] == nm_),
                                                         "%s点" % format(sum(int(float(r["points"] or 0)) for r in svc if r["service"] == nm_), ","), "") for sid, nm_ in WORLD_SVC if nm_ not in HIDE_SVC_HUB], key=lambda x: -x[1]),
                  "各サービスのアニメランキング（27か国）の点数を全部足した数です。大きいほど、そのサービスでアニメがたくさん観られています。") +
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
        body = ("<h1>%sで人気のアニメ TOP%d（全配信サービス合計）</h1><p class=\"lead\">%sの配信サービス全体で、いま人気のアニメ（JustWatch 集計、%s）。</p>%s%s" % (
            esc(cname), len(items), esc(cname), esc(snap),
            decade_chart("%sで人気の作品は、いつの作品？" % esc(cname), [int(r["year"]) if (r.get("year") or "").isdigit() else None for r in rows[:30]],
                         "%sの TOP30 の作品を、放送・公開された年代ごとに数えました。" % esc(cname)), rank_list(items, label="%s（全配信合計）" % cname, href="country/%s.html" % cc.lower())))
        write("country/%s.html" % cc.lower(), page("%sで人気のアニメランキング" % cname, body, "%sの配信サービス全体で人気のアニメTOP%d" % (cname, len(items)), 1, banner="country"))
        lis = "".join('<li><span class="rk">%d</span>%s<span class="nm">%s</span></li>' % (i["rank"], img(i.get("img"), i["title"], "cvs"), esc(i["title"])) for i in items[:3])
        cards.append('<a class="svc svc-link" href="country/%s.html"><h3>%s</h3><ol>%s</ol><span class="more">TOP30を見る →</span></a>' % (cc.lower(), esc(cname), lis))
    country_cards.append("<h2>%s</h2><div class=\"svcgrid\">%s</div>" % (region, "".join(cards)))
body = ("<h1>国別アニメランキング（全配信サービス合計）</h1><p class=\"lead\">世界27か国で、それぞれの国の配信サービス全体を合わせたアニメ人気ランキング（集計日 %s）。</p>" % esc(snap)) + bar_chart(
    "TOP30に入った国の数（TOP10）", [(tlink(FIX_TITLE.get(r.get("title_ja") or r["title"], r.get("title_ja") or r["title"])), int(r["countries_in_top30"] or 0), "%sか国（1位は%sか国）" % (r["countries_in_top30"], r.get("top1_countries") or 0), "")
                                 for r in now_w if r["title"] not in EXCLUDE and (r.get("title_ja") or "") not in EXCLUDE][:10],
    "世界27か国のうち、何か国で TOP30 に入ったかの数です。") + "".join(country_cards)
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
    b = "<h1>%s アニメ おすすめランキング TOP30</h1><p class=\"lead\">世界評価（AniList スコア）順の%sジャンル TOP30。</p>%s%s" % (
        esc(name), esc(name), decade_chart("%sの名作は、いつの作品？" % esc(name), [int(r["season_year"]) if str(r.get("season_year") or "").isdigit() else None for r in rows],
                                           "歴代・世界評価の上位に入った%sジャンルの%d作品を、放送・公開された年代ごとに数えました。" % (esc(name), len(rows))), rank_list([dict(it, rank=i) for i, it in enumerate(anilist_items(rows, 30), 1)]))
    write(fn, page("%s アニメ おすすめランキング" % name, b, "%sジャンルのおすすめアニメTOP30" % name, 1, banner="genre"))
genre_bar = bar_chart("名作が多いジャンル", [('<a href="genre/%s.html">%s</a>' % (g.lower().replace(" ", "-"), esc(GENRE_JA.get(g, g))), len(rows), "%d作品" % len(rows), "")
                                         for g, rows in sorted(genre_map.items(), key=lambda kv: -len(kv[1])) if len(rows) >= 10][:12],
                      "歴代・世界評価の上位作品に、そのジャンルが何本入っているかの数です。", ranked=False)
write("genre.html", page("ジャンル別おすすめアニメ", "<h1>ジャンル別おすすめアニメ</h1>%s<ul class=\"links\">%s</ul>" % (genre_bar, "".join(links)), banner="genre", hero=True))

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
    b = "<h1>%d年のおすすめアニメ TOP%d</h1><p class=\"lead\">%d年に放送・公開された作品を世界評価（AniList スコア）順に。</p>%s%s%s%s" % (
        y, len(rows), y, prev_next, genre_chart("%d年に多かったジャンル" % y, [r.get("genres") for r in rows],
                                                "%d年のおすすめ TOP%d に、それぞれのジャンルの作品が何本あるかの数です（1作品に複数のジャンルがあります）。" % (y, len(rows))), rank_list([dict(it, rank=i) for i, it in enumerate(anilist_items(rows, 30), 1)]), prev_next)
    write(fn, page("%d年のおすすめアニメ" % y, b, "%d年に放送されたアニメのおすすめランキングTOP%d" % (y, len(rows)), 1, banner="year"))
ydiv = "".join('<div class="yrow"><span class="ydec">%d年代</span><div class="ylinks">%s</div></div>' % (d, "".join(v))
               for d, v in sorted(year_links.items(), reverse=True))
dec_c = collections.Counter()
for y_, v_ in by_year.items(): dec_c[(y_ // 10) * 10] += len(v_)
year_bar = bar_chart("年代ごとの人気作品の数", [("%d年代" % d, n_, "%d作品" % n_, "") for d, n_ in sorted(dec_c.items(), reverse=True)],
                     "このサイトで年別ページに使っている人気作品（AniList でリストに入れた人が一定数以上）の数です。", ranked=False)
write("year.html", page("年別おすすめアニメ", "<h1>年別おすすめアニメ</h1><p class=\"lead\">生まれた年や思い出の年から、好きな作品を探せます。1970年から今年まで、その年に放送・公開されたアニメを世界評価順に紹介します。</p>%s%s" % (year_bar, ydiv),
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

TRENDS = read_json(os.path.join(HERE, "trends.json")) if os.path.exists(os.path.join(HERE, "trends.json")) else {}
CHART_COLORS = ["#ff6b9d", "#ffb36b", "#ffe066", "#7bd88f", "#4fc3f7", "#7c8cff", "#c58bff", "#ff8a65", "#4dd0b8", "#e0e0e0"]
def rank_chart(y, c, n=10):
    """季節ページの「毎月の順位の動き」: AniList の人気（リストに入れた人の数）の日ごとの記録から、
    各月末（今月は最新の日）の時点で、その季節の作品の中で何位だったかを線で描く。月が 3 つ未満のときは毎週の順位"""
    rows = season_rows(y, c)
    series = {r["anilist_id"]: TRENDS.get(r["anilist_id"]) or {} for r in rows if r.get("anilist_id")}
    days = sorted({d for v in series.values() for d in v})
    if not days: return ""
    start = datetime.date(y, {"冬": 1, "春": 4, "夏": 7, "秋": 10}[c], 1).isoformat()
    days = [d for d in days if d >= start]
    if not days: return ""
    last = days[-1]
    month_ends = sorted({max(d for d in days if d[:7] == m) for m in {d[:7] for d in days}})
    if len(month_ends) >= 3:
        pts, unit = month_ends, "毎月"
        lab = lambda d: "%d月%s" % (int(d[5:7]), "" if d == last else "末")
    else:
        dd = [datetime.date.fromisoformat(d) for d in days]
        pts = sorted({d.isoformat() for d in dd if d.weekday() == 6} | {last})
        pts = [d for d in pts if d >= days[0]]
        unit = "毎週"
        lab = lambda d: "%d/%d" % (int(d[5:7]), int(d[8:10]))
    def val(v, d):
        ks = [k for k in v if k <= d]
        return v[max(ks)] if ks else None
    ranks = {}
    for d in pts:
        vals = sorted(((val(v, d), aid) for aid, v in series.items() if val(v, d) is not None), key=lambda x: -x[0])
        for i, (_, aid) in enumerate(vals, 1): ranks.setdefault(aid, {})[d] = i
    top = sorted((aid for aid in ranks if last in ranks[aid]), key=lambda a: ranks[a][last])[:n]
    if not top: return ""
    name = {r["anilist_id"]: jp_title(r) for r in rows}
    ymax = min(30, max(ranks[a][d] for a in top for d in ranks[a]))
    W, H, L, R, T, B = 640, 300, 34, 26, 14, 30
    xs = lambda i: L + (W - L - R) * (i / max(1, len(pts) - 1))
    ys = lambda rk: T + (H - T - B) * ((min(rk, ymax) - 1) / max(1, ymax - 1))
    g = []
    for rk in sorted({1, 5, 10, 15, 20, 25, 30} & set(range(1, ymax + 1))):
        g.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="rc-g"/><text x="%d" y="%.1f" class="rc-y">%d位</text>' % (L, ys(rk), W - R, ys(rk), L - 4, ys(rk) + 4, rk))
    for i, d in enumerate(pts):
        g.append('<text x="%.1f" y="%d" class="rc-x">%s</text>' % (xs(i), H - 8, lab(d)))
    lines = []
    for j, a in enumerate(reversed(top)):
        col = CHART_COLORS[(len(top) - 1 - j) % len(CHART_COLORS)]
        xy = [(xs(i), ys(ranks[a][d])) for i, d in enumerate(pts) if d in ranks[a]]
        if len(xy) > 1:
            lines.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5" stroke-linejoin="round" class="rc-l"/>' % (" ".join("%.1f,%.1f" % p_ for p_ in xy), col))
        lines.append("".join('<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s"/>' % (x_, y_, col) for x_, y_ in xy))
    legend = "".join('<li><i style="background:%s"></i><b>%d位</b>%s%s</li>' % (
        CHART_COLORS[i % len(CHART_COLORS)], ranks[a][last], tlink(name.get(a, "")),
        (lambda f: (' <span class="rc-d up">↑%d</span>' % (f - ranks[a][last])) if f > ranks[a][last] else ((' <span class="rc-d dn">↓%d</span>' % (ranks[a][last] - f)) if f < ranks[a][last] else ""))(ranks[a][pts[0]] if pts[0] in ranks[a] else ranks[a][last]))
        for i, a in enumerate(top))
    lines = ('<defs><clipPath id="rcclip"><rect x="0" y="0" width="%d" height="%d"><animate attributeName="width" from="0" to="%d" dur="2.4s" begin="indefinite" fill="freeze" '
             'calcMode="spline" keyTimes="0;1" keySplines=".45 0 .25 1"/></rect></clipPath></defs><g clip-path="url(#rcclip)">%s</g>' % (W, H, W, "".join(lines)))
    return ('<section class="rchart" data-anim><h2>%sの順位の動き（TOP%d）</h2>'
            '<svg viewBox="0 0 %d %d" class="rc-svg" role="img" aria-label="%d年%sアニメ TOP%d の%sの順位の動き">%s%s</svg>'
            '<ol class="rc-lg">%s</ol><p class="note">AniList で作品を「観る・観たいリスト」に入れた人の数を%sの時点で比べ、この季節の%d作品の中での順位にしました。'
            '矢印は%sからの順位の変化です（%s 時点）。下のランキングは毎月の集計の時点の順位なので、順番が少し違うことがあります。</p></section>'
            % (unit, len(top), W, H, y, c, len(top), unit, "".join(g), lines, legend, "月末（今月は最新の日）" if unit == "毎月" else "毎週日曜（最後は最新の日）",
               len(series), lab(pts[0]), last))

def pop_chart(rows, h2, n=10):
    items = []
    for r in rows[:n]:
        try: pop = int(r.get("popularity") or 0)
        except ValueError: pop = 0
        items.append((tlink(jp_title(r)), pop, "%s人" % format(pop, ","), ""))
    return bar_chart(h2, items, "AniList で作品を「観る・観たいリスト」に入れた人の数（いまの数）です。")

def season_body(y, c, kind):
    """kind: current（今季）/ prev（前季）/ archive（それより前）"""
    rows = season_rows(y, c)
    lab = "%d年%sアニメ" % (y, c)
    lead = {"current": "今期の1話目、どれから観るか決められます。今期（%d年%sクール）に放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べました。「Filmarks で話題」は国内のレビューサイトでも話題になっている作品です。" % (y, c),
            "prev": "見逃した作品を、配信でまとめて観るのに役立ちます。前期（%d年%sクール）に放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べました。" % (y, c),
            "archive": "あの頃夢中だった作品に、また会えます。%d年%sクールに放送が始まったアニメを、世界の視聴者の注目度（AniList の人気）順に並べた記録です。" % (y, c)}[kind]
    # 個別ページを作るのは今季・前季の作品だけ（過去の全シーズン分は数が多すぎるため）
    label = lab if kind in ("current", "prev") else None
    href = {"current": "season.html", "prev": "prev-season.html"}.get(kind)
    return "<h1>%s 人気ランキング TOP30</h1><p class=\"lead\">%s</p>%s%s" % (esc(lab), lead,
           rank_chart(y, c) if kind in ("current", "prev") else pop_chart(rows, "その季節の人気の大きさ（TOP10）"),
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
body = ("<h1>シーズン別アニメランキング</h1><p class=\"lead\">あなたが観ていたあの季節のアニメに、すぐたどり着けます。1970年から今期まで、クール（冬・春・夏・秋）ごとに放送が始まったアニメの人気ランキングをまとめました。</p>"
        + '<div class="grid">%s%s</div>' % (mini(season_items(season_rows(SEASON_Y, SEASON_C)), "season.html", "今季：" + season_label),
                                           mini(season_items(season_rows(PREV_Y, PREV_C), hot_flag=False), "prev-season.html", "前季：" + prev_label))
        + pop_chart(season_rows(SEASON_Y, SEASON_C), "今季いちばん注目の10本")
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
<p class="vh">あなたが今夜観る1本が見つかります。世界27か国・国内13サービスの配信ランキングと歴代の評価データから、いま人気のアニメを毎月更新で紹介します。</p></section>""" if HERO_IMG else
"""<section class="hero"><h1>%s</h1>
<p>あなたが今夜観る1本が見つかります。世界27か国・国内13サービスの配信ランキングと歴代の評価データから、いま人気のアニメを毎月更新で紹介します。</p></section>""") + """
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
body = body.replace('<div class="grid">', trend_chart(now_w, PREV_W) + '<div class="grid">', 1)
write("index.html", page("トップ", body, "あなたが今夜観る1本が見つかる。配信ランキングと歴代評価でえらぶおすすめアニメ"))

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

# ---------- Prime Video の作品リンク（affiliate.json の prime_video: {作品名: Amazon アソシエイトの URL}。2026-10-25 追加） ----------
_PV = {norm(k): v for k, v in (CFG.get("prime_video") or {}).items()}
def prime_link(title):
    n = norm(title)
    for k, v in _PV.items():
        if k and (k == n or (k in n and len(n) - len(k) <= 6)):
            return v
    return ""
SVC_FROM_RANK = {"ABEMA 日本": "ABEMA", "DMM TV 日本": "DMM TV", "TVer 日本": "TVer", "バンダイチャンネル 日本": "バンダイチャンネル"}
index_out = []
# 作品ページの「世界評価くらべ」用に、ジャンルごとの平均点（ある程度観られている作品だけ）
_gs = collections.defaultdict(list)
for r_ in seasonal:
    try: sc_, pp_ = int(r_.get("average_score") or 0), int(r_.get("popularity") or 0)
    except ValueError: continue
    if sc_ and pp_ >= 2000 and not is_adult(r_):
        for g_ in (r_.get("genres") or "").split("|"):
            if g_: _gs[g_].append(sc_)
GENRE_AVG = {g_: sum(v_) / len(v_) for g_, v_ in _gs.items() if len(v_) >= 20}
def pop_line(t, m):
    """今季・前季の作品は、AniList で「観る・観たいリスト」に入れた人の数の伸びを折れ線にする（毎週日曜＋最新の日）"""
    v = TRENDS.get(str(m.get("anilist_id") or "")) if m else None
    if not v or len(v) < 3: return ""
    days = sorted(v)
    pts = [d for d in days if datetime.date.fromisoformat(d).weekday() == 6] + [days[-1]]
    pts = sorted(set(d for d in pts if d >= days[0]))
    if len(pts) < 3: pts = days
    if len(pts) > 16: pts = pts[-16:]
    vals = [v[d] for d in pts]
    lo, hi = min(vals), max(vals)
    if hi <= lo: return ""
    W, H, L, R, T, B = 640, 220, 62, 26, 14, 30
    xs = lambda i: L + (W - L - R) * (i / max(1, len(pts) - 1))
    ys = lambda x: T + (H - T - B) * (1 - (x - lo) / (hi - lo))
    g = ['<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="rc-g"/><text x="%d" y="%.1f" class="rc-y">%s人</text>' % (L, ys(x), W - R, ys(x), L - 4, ys(x) + 4, format(int(x), ","))
         for x in (lo, (lo + hi) / 2, hi)]
    step = max(1, len(pts) // 6)
    g += ['<text x="%.1f" y="%d" class="rc-x">%d/%d</text>' % (xs(i), H - 8, int(d[5:7]), int(d[8:10])) for i, d in enumerate(pts) if i % step == 0 or i == len(pts) - 1]
    xy = [(xs(i), ys(x)) for i, x in enumerate(vals)]
    area = "%.1f,%d %s %.1f,%d" % (xy[0][0], H - B, " ".join("%.1f,%.1f" % q for q in xy), xy[-1][0], H - B)
    body = ('<polygon points="%s" class="pl-a"/><polyline points="%s" fill="none" stroke="#ff6b9d" stroke-width="2.5" stroke-linejoin="round"/>%s'
            % (area, " ".join("%.1f,%.1f" % q for q in xy), "".join('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#ff6b9d"/>' % q for q in xy)))
    clip = ('<defs><clipPath id="plclip"><rect x="0" y="0" width="%d" height="%d"><animate attributeName="width" from="0" to="%d" dur="2s" begin="indefinite" fill="freeze" '
            'calcMode="spline" keyTimes="0;1" keySplines=".45 0 .25 1"/></rect></clipPath></defs><g clip-path="url(#plclip)">%s</g>' % (W, H, W, body))
    grow = vals[-1] - vals[0]
    return ('<section class="rchart" data-anim><h2>「観たい」人の数の伸び</h2><svg viewBox="0 0 %d %d" class="rc-svg" role="img" aria-label="%sの人気の伸び">%s%s</svg>'
            '<p class="note">AniList で「%s」を「観る・観たいリスト」に入れた人の数です（毎週日曜と最新の日、%s 時点）。%s/%d から %s人増えました。</p></section>'
            % (W, H, esc(t), "".join(g), clip, esc(t), pts[-1], int(pts[0][5:7]), int(pts[0][8:10]), format(grow, ",")))
def near_chart(k, d):
    """数字の少ない作品は、載っているランキングで前後の順位の作品と並べる（この作品は太字）"""
    apps_ = [a for a in d["apps"] if str(a[1]).isdigit()]
    if not apps_: return ""
    lab, rk, hr = apps_[0][0], int(apps_[0][1]), apps_[0][2]
    same = sorted({(int(a[1]), k2) for k2, d2 in TITLE_DB.items() for a in d2["apps"] if a[0] == lab and a[2] == hr and str(a[1]).isdigit() and int(a[1]) <= 30})
    i = [x[1] for x in same].index(k) if k in [x[1] for x in same] else None
    if i is None: return ""
    win = same[max(0, i - 3): i + 4]
    rows_ = [(("<b>%s</b>" % esc(TITLE_DB[k2]["title"])) if k2 == k else ('<a href="%s.html">%s</a>' % (k2, esc(TITLE_DB[k2]["title"]))), 31 - r_, "%d位" % r_, "") for r_, k2 in win]
    return bar_chart("「%s」で近い順位の作品" % esc(lab), rows_, "棒が長いほど上の順位です。近い順位の作品も、次に観る候補にどうぞ。", ranked=False, mx=30)
def apps_chart(apps):
    """世界評価が無い作品は、各ランキングでの順位を棒にする（上の順位ほど長い）"""
    rows_ = [(esc(lab), 31 - int(rk), "%s位" % rk, "") for lab, rk, h, sb in sorted(apps, key=lambda a: int(a[1]) if str(a[1]).isdigit() else 99)
             if str(rk).isdigit() and int(rk) <= 30][:8]
    return bar_chart("ランキングでの順位くらべ", rows_, "棒が長いほど、そのランキングで上の順位です（1位がいちばん長い）。", ranked=False, mx=30)
def score_chart(t, m):
    try: sc = int(float(m.get("average_score") or 0)) if m else 0
    except ValueError: sc = 0
    if not sc: return ""
    rows_ = [("<b>%s</b>" % esc(t), sc, "%d点" % sc, "")]
    for g_ in [x for x in (m.get("genres") or "").split("|") if x in GENRE_AVG and GENRE_JA.get(x, x)][:4]:
        rows_.append(("%sの平均" % esc(GENRE_JA.get(g_, g_)), GENRE_AVG[g_], "%.0f点" % GENRE_AVG[g_], ""))
    return bar_chart("世界評価くらべ", rows_, "AniList の平均スコア（100点満点）です。ジャンルの平均は、そのジャンルである程度観られている作品の平均点です。", ranked=False, mx=100)
# 「これが好きなら次はこの5本」用に、作品ごとの特徴（ジャンル・評価・見放題サービス・形式）を先にまとめる
FEAT = {}
for k_, d_ in TITLE_DB.items():
    m_ = meta_for(d_)
    if not m_ or not m_.get("genres"): continue
    try: sc_ = float(m_.get("average_score") or 0)
    except ValueError: sc_ = 0
    w_ = WATCH.get(k_) or {}
    FEAT[k_] = {"title": d_["title"], "g": set(x for x in m_["genres"].split("|") if GENRE_JA.get(x, x)), "sc": sc_,
                "flat": set(w_.get("flatrate") or []), "movie": m_.get("format") == "MOVIE", "base": norm(unicodedata.normalize("NFKC", strip_extra(d_["title"])))[:4]}
def next_five(k):
    """同じジャンルが多い・評価が近い・同じサービスで見放題・形式が同じ、の順に重みを付けて 5 本選ぶ。同じシリーズは 1 本まで（自分のシリーズも含む）"""
    me = FEAT.get(k)
    if not me: return []
    cand = []
    for k2, f in FEAT.items():
        if k2 == k: continue
        inter = me["g"] & f["g"]   # ジャンルが重ならない作品も、5 本に足りないときの補欠として点数を付けておく
        s_ = 3.0 * len(inter) / len(me["g"] | f["g"]) + (2.0 if inter else 0)
        if me["sc"] and f["sc"]: s_ += 1.0 - min(abs(me["sc"] - f["sc"]), 20) / 20.0
        s_ += 0.4 * (f["sc"] / 100.0)
        if me["flat"] & f["flat"]: s_ += 0.5
        if me["movie"] == f["movie"]: s_ += 0.3
        cand.append((s_, k2, inter))
    cand.sort(key=lambda x: -x[0])
    out, used = [], {me["base"]}   # 自分と同じシリーズはすすめない
    for s_, k2, inter in cand:
        b = FEAT[k2]["base"]
        if b in used: continue
        used.add(b)
        out.append((k2, inter))
        if len(out) == 5: break
    return out
POPULAR_KEYS = [kk for kk in dict.fromkeys(tkey(i["title"]) for i in now_items(now_w, n=40)) if kk in FEAT]
def next_block(k):
    picks = next_five(k)
    if not picks:   # ジャンルの情報が無い作品は、いま世界で人気の作品から 5 本
        pop = [kk for kk in POPULAR_KEYS if kk != k][:5]
        if not pop: return ""
        lis = "".join('<li><a href="%s.html">%s</a></li>' % (kk, esc(FEAT[kk]["title"])) for kk in pop)
        return '<h2>迷ったら、いま世界で人気のこの5本</h2><ol class="nx">%s</ol>' % lis
    lis = []
    for k2, inter in picks:
        f = FEAT[k2]
        bits = (["ジャンル: " + "・".join(GENRE_JA.get(x, x) for x in sorted(inter)[:3])] if inter
                else ["ジャンル: " + "・".join(GENRE_JA.get(x, x) for x in sorted(f["g"])[:3])])
        if f["sc"]: bits.append("世界評価 %d点" % f["sc"])
        if f["flat"]: bits.append("見放題: " + "・".join(sorted(f["flat"])[:2]) + (" ほか" if len(f["flat"]) > 2 else ""))
        lis.append('<li><a href="%s.html">%s</a><span class="nx-s">%s</span></li>' % (k2, esc(f["title"]), esc(" ／ ".join(bits))))
    return ('<h2>これが好きなら、次はこの5本</h2><ol class="nx">%s</ol>'
            '<p class="note">同じジャンル・近い評価・同じサービスで見放題、の順に近い作品を選んでいます（同じジャンルが5本に足りないときは、評価や配信が近い作品で補っています）。</p>' % "".join(lis))

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
        pv = prime_link(t)
        if pv:
            rows_.append('<div class="wrow"><span class="wlb">Prime Video</span><a class="btn amz" rel="nofollow sponsored noopener" target="_blank" href="%s">Prime Video で観る（レンタル・購入）</a></div>' % esc(pv))
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
            '<h2>ランキングでの順位</h2><table class="apps">%s</table>' % apps + (score_chart(t, m) or apps_chart(d["apps"]) or (near_chart(k, d) if not (m and TRENDS.get(str(m.get("anilist_id") or ""))) else "")) + pop_line(t, m) +
            goods_block(t, *goods_pick(k, m)) +
            '<h2>Blu-ray・原作・グッズ</h2>' + shop_buttons(t) +
            next_block(k))
    desc = "%sはどこで観られる？配信サービス・ランキング順位・%sまとめ" % (t, "名言・" if kg else "")
    write("anime/%s.html" % k, page("%sはどこで観られる？配信・ランキングまとめ" % t, body, desc, 1))
json.dump(index_out, open(os.path.join(HERE, "titles_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 固定ページ ----------
write("about.html", page("このサイトについて", """<h1>このサイトについて</h1>
<p>見に来てくださって、ありがとうございます。「%s」では、あなたが次に観るアニメを、世界と日本の配信ランキング・レビューサイトの評価データから選べます。データは毎月集計し、個人で運営しています。</p>
<h2>データの出典</h2>
<ul><li>AniList（世界最大級のアニメデータベース）: 歴代評価・ジャンル・年別</li>
<li>Netflix Tudum 公式 Top 10: 週間ランキング・再生回数</li>
<li>JustWatch: 各国・各配信サービスの人気ランキング</li>
<li>ABEMA・DMM TV・TVer・バンダイチャンネル: 各サービスのランキング画面</li>
<li>Filmarks: 話題のアニメ・5段階評価</li></ul>
<p>配信サービスのアイコンは JustWatch より。</p>
<h2>画像と AI の利用について</h2><p>バナーなどの画像は画像生成AIまたはプログラムで作成し、作品紹介の文の下書きにAIを使い、運営者が公式情報で確認しています。特定の作品・キャラクターの画像は使っていません。</p>
<h2>運営者</h2><p>Masabee（YouTube: <a href="https://www.youtube.com/@Masabee1029" target="_blank" rel="noopener">@Masabee1029</a>）。運営者もアニメと音楽の推し活が好きで、「次に何を観よう」と迷う時間を、作品を楽しむ時間に変えられるように集計しています。</p>
<p>あなたの、いちばん好きなアニメは何ですか？　このサイトが、その次の1本に出会うきっかけになればうれしいです。</p>
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
.btn.vod{font-weight:700}ol.rank li.rv{opacity:0;transform:translateX(28px)}ol.rank li.rv.in{opacity:1;transform:none;transition:opacity .5s ease,transform .6s cubic-bezier(.2,.8,.2,1)}ol.rank li.rv .rk{display:inline-block}ol.rank li.in .rk{animation:rkpop .6s .15s cubic-bezier(.3,1.6,.5,1) both}ol.rank li.in .cv{animation:cvflip .7s .1s ease both}ol.rank li.in .sc-m i{animation:scfill 1s .35s ease-out both}.cv.tile{position:relative;overflow:hidden}.cv.tile:after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 35%,rgba(255,255,255,.45) 50%,transparent 65%);transform:translateX(-120%)}ol.rank li.in .cv.tile:after{animation:shine 1.1s .6s ease both}ol.rank li .cv{transition:transform .25s}ol.rank li:hover .cv{transform:translateY(-4px) rotate(-3deg) scale(1.05)}@keyframes rkpop{0%{transform:scale(.3);opacity:0}100%{transform:scale(1);opacity:1}}@keyframes cvflip{0%{transform:perspective(400px) rotateY(80deg);opacity:0}100%{transform:none;opacity:1}}@keyframes scfill{from{width:0}}@keyframes shine{to{transform:translateX(120%)}}
.tile{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;text-shadow:0 1px 3px rgba(0,0,0,.35)}.cv.tile span{font-size:2rem}.cvs.tile{display:inline-flex}.cvs.tile span{font-size:.85rem}
.cvs{display:inline-block;width:28px;height:40px;object-fit:cover;border-radius:3px;vertical-align:middle;margin-right:6px;background:#222}
.body{flex:1;min-width:0}.tt{font-weight:700;font-size:1.05rem;line-height:1.5;margin-bottom:4px}.sub,.meta{font-size:.82rem;color:var(--mu);line-height:1.7}
.shop{margin-top:12px}.shop-lb{display:block;font-size:.72rem;color:var(--mu);margin-bottom:4px;letter-spacing:.02em}
.shop-btns{display:flex;flex-wrap:wrap;gap:8px}
.btn{--bc:#888;font-size:.75rem;padding:3px 12px;border-radius:999px;text-decoration:none;background:#fff;color:color-mix(in srgb,var(--bc) 65%,#000);border:2px solid var(--bc);transition:background .15s}
.btn:hover{background:#fff8e6}
.btn.amz{--bc:#ff9900;color:#b35c00}.btn.rkt{--bc:#bf0000;color:#bf0000}.btn.yho{--bc:#ff0033;color:#d6002e}
/* 2026-10-30 本人指示: 暗い背景に合わせたボタン（白地をやめる） */
.btn{background:#232733;color:color-mix(in srgb,var(--bc) 55%,#fff);font-weight:800}.btn:hover{background:#2e3342}.btn.amz{--bc:#ffad33;color:#ffc266;border-color:#ffad33;box-shadow:0 0 10px #ffad3333}.btn.rkt{--bc:#ff5c7a;color:#ff8fa3;border-color:#ff5c7a;box-shadow:0 0 10px #ff5c7a33}.btn.yho{--bc:#ff4d6d;color:#ff8fa3;border-color:#ff4d6d}
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
.vcad{display:flex;flex-direction:column;gap:4px;padding:8px 0;border-top:1px solid var(--line)}.vcad span{font-size:.85rem;color:var(--mu)}.vcad .sbtn{align-self:flex-start}
.rchart{margin:8px 0 24px}.rc-svg{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}.rc-g{stroke:var(--line);stroke-width:1}.rc-y{fill:var(--mu);font-size:11px;text-anchor:end}.rc-x{fill:var(--mu);font-size:11px;text-anchor:middle}.rc-lg{list-style:none;padding:0;margin:10px 0 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 16px;font-size:.88rem}@media(max-width:640px){.rc-lg{grid-template-columns:1fr}}.rc-lg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}.rc-lg b{margin-right:6px;color:var(--mu);font-weight:600}.rc-d{font-size:.78rem;font-weight:700}.rc-d.up{color:#7bd88f}.rc-d.dn{color:#ff8a65}
.trend{margin:8px 0 24px}.tr-list{list-style:none;padding:0;margin:0}.tr-list li{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-bottom:1px solid var(--line)}.tr-rk{min-width:1.6em;font-weight:700;color:var(--ac);text-align:right}.tr-main{flex:1;min-width:0}.tr-nm{font-size:.95rem;margin-bottom:4px}.tr-bar{position:relative;height:14px;background:var(--line);border-radius:9px;overflow:hidden}.tr-bar span{display:block;height:100%;background:linear-gradient(90deg,#ff6b9d,#ffb36b);border-radius:9px;transform-origin:left;animation:trg .9s ease-out both}.tr-row{display:flex;align-items:center;gap:8px}.tr-row .tr-bar{flex:1}.tr-row em{font-size:.75rem;font-style:normal;color:var(--mu);white-space:nowrap;min-width:6.5em;text-align:right}@keyframes trg{from{transform:scaleX(0)}to{transform:scaleX(1)}}.pl-a{fill:#ff6b9d;opacity:.12}.sc{display:flex;align-items:baseline;gap:6px;margin:4px 0 2px;flex-wrap:wrap}.sc-l{font-size:.78rem;color:var(--mu)}.sc-n{font-size:1.9rem;line-height:1;font-weight:800;color:#ffd166;letter-spacing:.01em}.sc-u{font-size:.85rem;color:var(--mu);margin-right:6px}.sc-m{align-self:center;display:inline-block;width:120px;height:8px;border-radius:6px;background:var(--line);overflow:hidden}.sc-m i{display:block;height:100%;background:linear-gradient(90deg,#ffb36b,#ffd166);border-radius:6px}.wait .tr-bar span{animation-play-state:paused}.wait.go .tr-bar span{animation-play-state:running}.tr-list.nr li{align-items:center}@media(prefers-reduced-motion:reduce){.tr-bar span{animation:none}}.nx{padding-left:1.4em}.nx li{margin:8px 0}.nx li a{font-weight:700}.nx-s{display:block;font-size:.82rem;color:var(--mu)}
.goods{background:var(--card,#1a1d29);border:1px solid var(--line);border-left:4px solid var(--ac);border-radius:10px;padding:12px 16px;margin:8px 0}.goods-n{font-weight:700;font-size:1.05rem;margin:0 0 4px}.goods-w{margin:0;color:var(--mu);font-size:.92rem}
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
for sid_, (nm_, jl_) in WIDE_LISTS.items():
    rows_ = []
    for it in jl_[:10]:
        d_ = TITLE_DB.get(tkey(it["title"]))
        n_ = len({a[0] for a in d_["apps"]}) if d_ else 1
        rows_.append((tlink(it["title"]), n_, "%dつ" % n_, ""))
    ch_ = bar_chart("%sの人気作は、ほかのランキングにもいくつ入っている？" % esc(nm_), rows_,
                    "このサイトのランキング（配信サービス・国・季節など）のうち、その作品が入っている数です。多いほど、いろいろな場所で人気です。", mx=max([r[1] for r in rows_] + [1]))
    PAGES["service/%s.html" % sid_] = PAGES["service/%s.html" % sid_].replace("\x00WIDE:%s\x00" % sid_, ch_)
for old_, new_ in ALIAS.items():
    if new_ in TITLE_PAGES:
        PAGES["anime/%s.html" % old_] = ('<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=%s.html">'
                                         '<link rel="canonical" href="%sanime/%s.html"><title>移動しました</title></head><body><a href="%s.html">新しいページへ</a></body></html>'
                                         % (new_, CFG["site_url"].rstrip("/") + "/", new_, new_))
flush()
print("generated", len([f for _, _, fs in os.walk(OUT) for f in fs]), "files in docs/")
