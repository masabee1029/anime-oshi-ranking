#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""トップのサムネイル画像（1200x630, OGP 兼用）を作る。
いま人気の作品のジャケットを敷き詰め、暗いグラデーションの上にサイト名を載せる。
"""
import csv, json, os, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.expanduser("~/knowledge-os/raw/anime/streaming")
OUT = os.path.join(HERE, "docs", "thumbnail.jpg")
CACHE_DIR = os.path.join(HERE, ".thumb_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CFG = json.load(open(os.path.join(HERE, "affiliate.json"), encoding="utf-8"))
COV = json.load(open(os.path.join(HERE, "covers.json"), encoding="utf-8"))
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_R = "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc"
EXCLUDE = {"ザ・スーパーマリオギャラクシー・ムービー", "The Legend of Korra", "Golden Axe", "Zootopia 2",
           "Miraculous: Les aventures de Ladybug et Chat Noir", "The Super Mario Bros. Movie", "Spider-Man"}

def norm(t):
    return re.sub(r"[\s　:：・!！?？\-－~～「」『』()（）]", "", (t or "")).lower()

# いま人気（国内→世界→Netflix）から画像のある作品を順に集める
urls = []
def take(path, cols):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if any(r.get(c) in EXCLUDE for c in cols): continue
        for c in cols:
            u = COV["by_title"].get(norm(r.get(c)))
            if u:
                if u not in urls: urls.append(u)
                break
take(os.path.join(ST, "japan_allservices_ranking.csv"), ("title", "original_title"))
take(os.path.join(ST, "world_allservices_ranking.csv"), ("title_ja", "title"))
take(os.path.join(ST, "netflix_anime_ranking_global.csv"), ("anime_title_ja", "show_title"))

W, H = 1200, 630
COLS, ROWS = 9, 4
cw, ch = 140, 210   # 2:3 のジャケット比
need = COLS * ROWS

def fetch(u):
    big = u.replace("/cover/medium/", "/cover/large/")
    fn = os.path.join(CACHE_DIR, os.path.basename(big))
    if not os.path.exists(fn):
        import subprocess
        for src in (big, u):
            r = subprocess.run(["curl", "-s", "-f", "-m", "20", "-A", "anime-oshi-ranking/1.0", "-o", fn, src])
            if r.returncode == 0 and os.path.getsize(fn) > 1000: break
            if os.path.exists(fn): os.remove(fn)
    return Image.open(fn).convert("RGB") if os.path.exists(fn) else None

imgs = []
for u in urls:
    im = fetch(u)
    if im: imgs.append(im)
    if len(imgs) >= need: break

canvas = Image.new("RGB", (W, H), (15, 17, 21))
# 少し斜めにずらして敷き詰める（列ごとに上下オフセット）
gap = 6
total_w = COLS * cw + (COLS - 1) * gap
x0 = (W - total_w) // 2
for i, im in enumerate(imgs):
    c, r = i % COLS, i // COLS
    tile = im.resize((cw, int(im.height * cw / im.width)))
    tile = tile.crop((0, 0, cw, min(ch, tile.height)))
    off = -60 if c % 2 else -10
    canvas.paste(tile, (x0 + c * (cw + gap), off + r * (ch + gap)))

# 暗いグラデーション（中央が濃い）
shade = Image.new("L", (W, H))
sd = ImageDraw.Draw(shade)
for y in range(H):
    d = abs(y - H * 0.55) / (H * 0.55)
    sd.line([(0, y), (W, y)], fill=int(235 - 120 * min(d, 1) ** 1.5))
dark = Image.new("RGB", (W, H), (12, 13, 18))
canvas = Image.composite(dark, canvas, shade)

draw = ImageDraw.Draw(canvas)
title = CFG.get("site_name", "推しアニメランキング")
ft = ImageFont.truetype(FONT_B, 96)
fs = ImageFont.truetype(FONT_R, 30)
fb = ImageFont.truetype(FONT_B, 24)

def center(text, font, y, fill):
    w = draw.textbbox((0, 0), text, font=font)[2]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)
    return w

# 上のバッジ
badge = "毎月更新"
bw = draw.textbbox((0, 0), badge, font=fb)[2] + 36
bx = (W - bw) // 2
draw.rounded_rectangle([bx, 180, bx + bw, 222], radius=21, outline=(255, 107, 157), width=2)
center(badge, fb, 186, (255, 107, 157))
# タイトル（「推し」だけピンク）
full_w = draw.textbbox((0, 0), title, font=ft)[2]
tx = (W - full_w) // 2
head = "推し" if title.startswith("推し") else ""
if head:
    draw.text((tx, 240), head, font=ft, fill=(255, 107, 157))
    tx += draw.textbbox((0, 0), head, font=ft)[2]
draw.text((tx, 240), title[len(head):], font=ft, fill=(255, 255, 255))
# 下線
draw.rectangle([(W - 120) // 2, 362, (W + 120) // 2, 367], fill=(255, 107, 157))
center("世界27か国・国内12サービスの配信ランキングと歴代評価から", fs, 392, (225, 225, 230))
center("「いま観るべきアニメ」がわかる", fs, 436, (225, 225, 230))

canvas.save(OUT, "JPEG", quality=88, optimize=True)
print("thumbnail", OUT, len(imgs), "covers")
