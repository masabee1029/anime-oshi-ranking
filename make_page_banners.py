#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ページごとのサムネイル（1200x630、OGP 兼用）を作る。
assets/banner/base.webp（トップの画像）のイラスト・王冠・グラフ・再生ボタンはそのまま使い、
右側のタイトル・吹き出し・説明文だけを消して、ページごとの文言で描き直す。
出力: assets/banner/<name>.jpg（build.py が docs/banner/ にコピーする）
"""
import os, json, datetime, random, sys
if "--force" not in sys.argv:   # 2026-10-29: ページのバナーは make_text_banners.py（文字と図形だけ）が正。上書きしないよう止める
    sys.exit("make_page_banners.py は使わない。make_text_banners.py を使う（2026-10-29）")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "assets", "banner", "base.webp")
OUTD = os.path.join(HERE, "assets", "banner")
FB = "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc"
FM = "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc"
PINK, PINK2, NAVY, GLOW, WHITE = (255, 77, 150), (255, 140, 190), (24, 20, 70), (120, 200, 255), (255, 255, 255)

COUR = {1: "冬", 2: "冬", 3: "冬", 4: "春", 5: "春", 6: "春", 7: "夏", 8: "夏", 9: "夏", 10: "秋", 11: "秋", 12: "秋"}
_t = datetime.date.today()
SEASON = "%d年%s" % (_t.year, COUR[_t.month])

# name: (吹き出し, 1 行目のピンク部分, 1 行目の白部分, 2 行目, 説明 1 行目, 説明 2 行目のうちピンク, 説明 2 行目の残り)
PAGES = {
    "season":   (SEASON, "今季", "アニメ", "人気ランキング", "今期スタートの新作アニメを", "世界の注目度順", "にTOP30で紹介"),
    "now-japan": ("毎月更新", "国内", "いま人気", "アニメTOP30", "Netflix・U-NEXT・dアニメストアなど", "国内の配信ランキング", "を合算"),
    "now-world": ("毎月更新", "世界", "いま人気", "アニメTOP30", "世界27か国の配信ランキングを合算", "いま世界で観られている", "アニメ"),
    "best-world": ("永久保存版", "歴代", "名作アニメ", "世界評価TOP100", "世界最大級のアニメデータベースで", "海外ファンが選んだ", "名作がわかる"),
    "netflix":  ("公式Top10", "Netflix", "", "アニメランキング", "Netflix公式の再生回数でわかる", "世界と日本", "で人気のアニメ"),
    "services": ("13サービス", "配信", "サービス別", "アニメランキング", "Netflix・Prime Video・U-NEXT・ABEMAなど", "サービスごとの", "人気アニメ"),
    "country":  ("27か国", "国別", "アニメ", "ランキング", "アメリカ・韓国・フランス・ブラジル…", "その国でいま人気", "のアニメがわかる"),
    "genre":    ("16ジャンル", "ジャンル別", "", "おすすめアニメ", "アクション・恋愛・SF・日常…", "好きなジャンルの名作", "が見つかる"),
    "year":     ("1970年〜", "年別", "おすすめ", "名作アニメ", "1970年から今年まで", "その年の名作", "がひと目でわかる"),
}

src = Image.open(BASE).convert("RGB")
W, H = src.size   # 1731 x 909

# ---- 1. 消す範囲（吹き出し・タイトル・説明文） ----
cover = Image.new("L", (W, H), 0)
cd = ImageDraw.Draw(cover)
cd.rounded_rectangle([680, 35, 1040, 195], 40, fill=255)                        # 吹き出し
cd.polygon([(582, 195), (1380, 195), (1380, 262), (1540, 262), (1540, 600), (1610, 575),
            (1610, 800), (700, 800), (690, 640), (655, 600), (582, 600)], fill=255)  # タイトル＋説明
cover = cover.filter(ImageFilter.MaxFilter(9))

# ---- 2. 背景を推定（右側の背景色を 2 次式で近似） ----
a = np.asarray(src).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W]
cov = np.asarray(cover) > 0
lum = a.mean(axis=2)
sel = (~cov) & (xx > 560) & (lum < 150)
def feats(x, y):
    x = x / W; y = y / H
    return np.stack([np.ones_like(x), x, y, x * x, y * y, x * y, x ** 3, y ** 3], axis=-1)
F = feats(xx[sel].astype(np.float32), yy[sel].astype(np.float32))
bg = np.zeros_like(a)
Fall = feats(xx.astype(np.float32), yy.astype(np.float32))
for c in range(3):
    coef, *_ = np.linalg.lstsq(F, a[..., c][sel], rcond=None)
    bg[..., c] = Fall @ coef
bg = np.clip(bg, 0, 255)

base = a.copy()
m = (np.asarray(cover.filter(ImageFilter.GaussianBlur(22))).astype(np.float32) / 255.0)[..., None]
base = base * (1 - m) + bg * m
img = Image.fromarray(base.astype(np.uint8))

# 消した場所に質感（斜めの光の線・小さな星）
tex = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(tex)
random.seed(11)
for _ in range(14):
    x = random.randint(600, 1550); y = random.randint(200, 780); l = random.randint(60, 180)
    td.line([(x, y), (x + l, y - l * 0.55)], fill=(150, 170, 255, random.randint(40, 90)), width=random.choice([3, 4, 6]))
for _ in range(40):
    x = random.randint(600, 1580); y = random.randint(40, 790); s = random.choice([1, 2, 2, 3])
    td.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, random.randint(80, 180)))
tmask = Image.fromarray((np.asarray(cover) > 0).astype(np.uint8) * 255)
img.paste(tex, (0, 0), Image.composite(tex.split()[3], Image.new("L", (W, H), 0), tmask))

# ---- 3. 王冠・グラフ・再生ボタンを元の画像から戻す ----
def restore(im, box, ell=True):
    mk = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mk)
    (md.ellipse if ell else md.rectangle)(box, fill=255)
    im.paste(src, (0, 0), mk.filter(ImageFilter.GaussianBlur(4)))
RESTORE = [((1375, 10, 1690, 270), True), ((520, 615, 800, 900), False), ((1495, 690, 1685, 880), True)]  # 王冠・グラフ・再生ボタン

def font(path, size): return ImageFont.truetype(path, size)

def text_w(d, s, f): return d.textbbox((0, 0), s, font=f)[2] if s else 0

def draw_title(d, x, y, parts, size, max_w):
    """parts: [(文字, 色)] を太い縁取りつきで描く。幅が max_w を超えたら縮める"""
    while True:
        f = font(FB, size)
        tw = sum(text_w(d, s, f) for s, _ in parts)
        if tw <= max_w or size < 60: break
        size -= 6
    cx = x
    for s, col in parts:
        if not s: continue
        d.text((cx, y), s, font=f, fill=GLOW, stroke_width=max(10, size // 7) + 8, stroke_fill=GLOW)
        cx += text_w(d, s, f)
    cx = x
    for s, col in parts:
        if not s: continue
        d.text((cx, y), s, font=f, fill=col, stroke_width=max(10, size // 7), stroke_fill=NAVY)
        cx += text_w(d, s, f)
    return size

def make(name, spec):
    bubble, p1, w1, line2, sub1, subp, subr = spec
    im = img.copy()
    d = ImageDraw.Draw(im)
    # 吹き出し
    fbub = font(FB, 52)
    bw = text_w(d, bubble, fbub) + 70
    bx0, by0 = 700, 55
    d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + 100], 50, fill=PINK, outline=WHITE, width=6)
    d.polygon([(bx0 + bw * 0.55, by0 + 94), (bx0 + bw * 0.72, by0 + 94), (bx0 + bw * 0.70, by0 + 140)], fill=PINK)
    d.line([(bx0 + bw * 0.70, by0 + 140), (bx0 + bw * 0.72, by0 + 97)], fill=WHITE, width=6)
    d.line([(bx0 + bw * 0.55, by0 + 97), (bx0 + bw * 0.70, by0 + 140)], fill=WHITE, width=6)
    d.text((bx0 + 35, by0 + 18), bubble, font=fbub, fill=WHITE)
    # タイトル 2 行
    draw_title(d, 610, 215, [(p1, PINK), (w1, WHITE)], 190, 1500 - 610 if not w1 or len(p1 + w1) > 4 else 900)
    draw_title(d, 690, 405, [(line2, WHITE)], 170, 1540 - 690)
    # 説明の白い帯
    poly = [(760, 615), (1500, 588), (1488, 758), (745, 785)]
    d.polygon([(x + 6, y + 8) for x, y in poly], fill=(60, 80, 160))
    d.polygon(poly, fill=(250, 250, 255), outline=GLOW)
    size = 44
    while size > 30 and max(text_w(d, sub1, font(FM, size)), text_w(d, "「" + subp + "」" + subr, font(FM, size))) > 1470 - 800:
        size -= 2
    fs = font(FM, size)
    d.text((800, 625), sub1, font=fs, fill=NAVY)
    x2 = 800
    d.text((x2, 690), "「" + subp + "」", font=fs, fill=PINK)
    d.text((x2 + text_w(d, "「" + subp + "」", fs), 690), subr, font=fs, fill=NAVY)
    for box, ell in RESTORE:
        restore(im, box, ell)
    out = im.resize((1200, 630), Image.LANCZOS)
    out.save(os.path.join(OUTD, name + ".jpg"), "JPEG", quality=90, optimize=True)

for n, s in PAGES.items():
    make(n, s)
print("banners:", ", ".join(PAGES))
