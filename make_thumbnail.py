#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""トップのサムネイル画像（1200x630, OGP 兼用）。
作品の絵は使わず、文字と図形だけで作るオリジナルデザイン（著作権対策 2026-10-12）。
"""
import json, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs", "thumbnail.jpg")
CFG = json.load(open(os.path.join(HERE, "affiliate.json"), encoding="utf-8"))
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_M = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc"
W, H = 1200, 630
PINK, GOLD, BG = (255, 107, 157), (255, 209, 102), (14, 15, 20)

img = Image.new("RGB", (W, H), BG)

# 背景: ぼかした光の玉（ピンク・金・青紫）
glow = Image.new("RGB", (W, H), BG)
g = ImageDraw.Draw(glow)
for (x, y, r, c) in [(150, 120, 260, (120, 40, 90)), (1080, 520, 300, (110, 80, 30)),
                     (980, 90, 200, (50, 50, 120)), (220, 560, 220, (60, 30, 100))]:
    g.ellipse([x - r, y - r, x + r, y + r], fill=c)
img = glow.filter(ImageFilter.GaussianBlur(110))

d = ImageDraw.Draw(img, "RGBA")
# 細かい星
random.seed(7)
for _ in range(140):
    x, y = random.randint(0, W), random.randint(0, H)
    s = random.choice([1, 1, 1, 2])
    d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, random.randint(60, 160)))

# 左下: ランキングの棒グラフ（1〜5位）
base_y, x0 = 590, 70
for i, hgt in enumerate([170, 130, 105, 80, 60]):
    x = x0 + i * 46
    col = GOLD if i == 0 else (PINK if i < 3 else (200, 200, 210))
    d.rounded_rectangle([x, base_y - hgt, x + 32, base_y], radius=6, fill=col + (200 if i < 3 else 90,))
# 右上: 王冠モチーフ
cx, cy = 1070, 120
crown = [(cx - 60, cy + 30), (cx - 60, cy - 20), (cx - 30, cy + 5), (cx, cy - 40), (cx + 30, cy + 5), (cx + 60, cy - 20), (cx + 60, cy + 30)]
d.polygon(crown, fill=GOLD + (220,))
for px in (cx - 60, cx, cx + 60):
    py = cy - 40 if px == cx else cy - 20
    d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=GOLD + (255,))
d.rectangle([cx - 60, cy + 36, cx + 60, cy + 48], fill=GOLD + (220,))
# 右下: 再生ボタン
px, py, pr = 1090, 520, 46
d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=PINK + (230,), width=5)
d.polygon([(px - 14, py - 22), (px - 14, py + 22), (px + 24, py)], fill=PINK + (230,))

def center(text, font, y, fill):
    w = d.textbbox((0, 0), text, font=font)[2]
    d.text(((W - w) // 2, y), text, font=font, fill=fill)

ft = ImageFont.truetype(FONT_B, 100)
fs = ImageFont.truetype(FONT_R, 30)
fb = ImageFont.truetype(FONT_M, 24)
title = CFG.get("site_name", "推しアニメランキング")

badge = "毎月更新"
bw = d.textbbox((0, 0), badge, font=fb)[2] + 40
bx = (W - bw) // 2
d.rounded_rectangle([bx, 168, bx + bw, 212], radius=22, outline=PINK, width=2)
center(badge, fb, 175, PINK)

full_w = d.textbbox((0, 0), title, font=ft)[2]
tx = (W - full_w) // 2
head = "推し" if title.startswith("推し") else ""
if head:
    d.text((tx, 232), head, font=ft, fill=PINK)
    tx += d.textbbox((0, 0), head, font=ft)[2]
d.text((tx, 232), title[len(head):], font=ft, fill=(255, 255, 255))
d.rectangle([(W - 120) // 2, 362, (W + 120) // 2, 367], fill=PINK)
center("世界27か国・国内13サービスの配信ランキングと歴代評価から", fs, 392, (228, 228, 235))
center("「いま観るべきアニメ」がわかる", fs, 436, (228, 228, 235))

img.save(OUT, "JPEG", quality=90, optimize=True)
print("thumbnail", OUT)
