#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ページごとのバナー（1200x630、OGP 兼用）を、文字と図形だけで作る。
2026-10-29: 実在のアニメキャラに似た AI 画像 7 枚を差し替えるために作成（make_thumbnail.py 方式）。
キャラクター・人物・実在のロゴは描かない。配信サービス名は文字だけ。日本語はプログラムで描くので崩れない。
出力: assets/banner/<name>.jpg（build.py が docs/banner/ にコピーする）
"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, "assets", "banner")
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_M = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc"
W, H = 1200, 630
PINK, GOLD, BG, WHITE, SUB = (255, 107, 157), (255, 209, 102), (14, 15, 20), (255, 255, 255), (228, 228, 235)
BLUE, GREEN, ORANGE, PURPLE = (110, 170, 255), (110, 220, 160), (255, 150, 70), (175, 130, 255)


def font(path, size): return ImageFont.truetype(path, size)


def background(seed, glows):
    glow = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(glow)
    for (x, y, r, c) in glows:
        g.ellipse([x - r, y - r, x + r, y + r], fill=c)
    img = glow.filter(ImageFilter.GaussianBlur(110))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(seed)
    for _ in range(120):
        x, y = random.randint(0, W), random.randint(0, H)
        s = random.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, random.randint(60, 150)))
    return img, d


def tw(d, text, f): return d.textbbox((0, 0), text, font=f)[2]


def badge(d, text, x, y, col=PINK):
    f = font(FONT_M, 26)
    w = tw(d, text, f) + 44
    d.rounded_rectangle([x, y, x + w, y + 48], radius=24, fill=col + (235,))
    d.text((x + 22, y + 8), text, font=f, fill=BG)


def title_block(d, x, y, line1, line2, desc1, desc2, size=84):
    """line1 = [(文字, 色), ...]、line2 も同じ。左寄せ"""
    f = font(FONT_B, size)
    for parts, yy in ((line1, y), (line2, y + size + 18)):
        xx = x
        for t, c in parts:
            d.text((xx, yy), t, font=f, fill=c)
            xx += tw(d, t, f)
    ly = y + 2 * (size + 18) + 14
    d.rectangle([x, ly, x + 110, ly + 6], fill=PINK)
    fs = font(FONT_R, 28)
    d.text((x, ly + 28), desc1, font=fs, fill=SUB)
    d.text((x, ly + 72), desc2, font=fs, fill=SUB)


def footer(d):
    f = font(FONT_M, 22)
    t = "推しアニメランキング"
    d.text((W - tw(d, t, f) - 40, H - 46), t, font=f, fill=(255, 255, 255, 150))


def bars(d, x0, base_y, heights, gap=46, bw=32):
    for i, hgt in enumerate(heights):
        x = x0 + i * gap
        col = GOLD if i == len(heights) - 1 else PINK
        d.rounded_rectangle([x, base_y - hgt, x + bw, base_y], radius=6, fill=col + (210,))


def save(img, name):
    p = os.path.join(OUTD, name + ".jpg")
    img.save(p, "JPEG", quality=90, optimize=True)
    print("banner", p)


# ---- year: 年表の線 ----
def make_year():
    img, d = background(1, [(150, 120, 260, (120, 40, 90)), (1080, 520, 300, (110, 80, 30)), (980, 90, 200, (50, 50, 120))])
    badge(d, "1970年〜", 70, 70)
    title_block(d, 70, 150, [("年別", PINK), ("おすすめ", WHITE)], [("名作アニメ", WHITE)],
                "1970年から今年まで", "その年の名作がひと目でわかる")
    y = 548
    d.line([(70, y), (1130, y)], fill=(255, 255, 255, 120), width=4)
    f = font(FONT_M, 24)
    labels = ["1970", "1980", "1990", "2000", "2010", "2020", "今年"]
    for i, t in enumerate(labels):
        x = 90 + i * 168
        c = GOLD if i == len(labels) - 1 else PINK
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=c + (255,))
        d.text((x - tw(d, t, f) // 2, y - 52), t, font=f, fill=SUB)
    # 右上: 積み上がる年のカード
    for i in range(5):
        x, yy = 780 + i * 34, 110 + i * 40
        d.rounded_rectangle([x, yy, x + 270, yy + 150], radius=14, fill=(30, 33, 44, 230), outline=PINK + (160,), width=2)
    fb = font(FONT_B, 54)
    d.text((780 + 4 * 34 + 30, 110 + 4 * 40 + 42), "年ごと", font=fb, fill=GOLD)
    footer(d)
    save(img, "year")


# ---- country: 地球（線だけ） ----
def make_country():
    img, d = background(2, [(160, 140, 260, (40, 60, 120)), (1040, 330, 320, (110, 40, 90)), (300, 560, 220, (60, 30, 100))])
    badge(d, "27か国", 70, 70)
    title_block(d, 70, 150, [("国別", PINK), ("アニメ", WHITE)], [("ランキング", WHITE)],
                "アメリカ・韓国・フランス・ブラジル…", "その国でいま人気のアニメがわかる")
    cx, cy, r = 930, 300, 200
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 50, 100, 200), outline=BLUE + (255,), width=5)
    for k in (0.35, 0.7):
        d.ellipse([cx - r * k, cy - r, cx + r * k, cy + r], outline=BLUE + (170,), width=3)
    d.line([(cx, cy - r), (cx, cy + r)], fill=BLUE + (170,), width=3)
    for dy in (-0.55, 0, 0.55):
        yy = cy + r * dy
        half = (r * r - (r * dy) ** 2) ** 0.5
        d.line([(cx - half, yy), (cx + half, yy)], fill=BLUE + (170,), width=3)
    random.seed(22)
    for _ in range(27):   # 27 か国を光の点で
        import math
        a = random.uniform(0, 2 * math.pi); rr = random.uniform(0, r * 0.92)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        c = random.choice([PINK, GOLD, WHITE])
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=c + (240,))
    footer(d)
    save(img, "country")


# ---- genre: ジャンル名のタグ（文字だけ） ----
GENRES = ["アクション", "冒険", "コメディ", "ドラマ", "ファンタジー", "ホラー", "ロボット", "音楽",
          "ミステリー", "心理", "恋愛", "SF", "日常", "スポーツ", "超常", "スリラー"]


def make_genre():
    img, d = background(3, [(150, 120, 260, (120, 40, 90)), (1000, 300, 320, (60, 40, 120)), (400, 580, 220, (110, 80, 30))])
    badge(d, "16ジャンル", 70, 70)
    title_block(d, 70, 150, [("ジャンル別", PINK)], [("おすすめアニメ", WHITE)],
                "アクション・恋愛・SF・日常…", "好きなジャンルの名作が見つかる", size=78)
    f = font(FONT_M, 25)
    cols = [PINK, GOLD, BLUE, GREEN, ORANGE, PURPLE]
    x0, y, x = 700, 70, 700
    for i, g in enumerate(GENRES):
        w = tw(d, g, f) + 40
        if x + w > 1150:
            x = x0 + (20 if (y // 70) % 2 == 0 else 0); y += 66
        c = cols[i % len(cols)]
        d.rounded_rectangle([x, y, x + w, y + 48], radius=24, fill=(30, 33, 44, 235), outline=c + (255,), width=3)
        d.text((x + 20, y + 9), g, font=f, fill=c)
        x += w + 14
    footer(d)
    save(img, "genre")


# ---- services: サービス名（文字だけ） ----
SERVICES = ["Netflix", "Prime Video", "U-NEXT", "dアニメストア", "ABEMA", "DMM TV", "Disney+",
            "Hulu", "FOD", "TVer", "Crunchyroll", "HBO Max", "バンダイチャンネル"]


def make_services():
    img, d = background(4, [(150, 120, 260, (120, 40, 90)), (1080, 520, 300, (40, 70, 130)), (980, 90, 200, (90, 40, 110))])
    badge(d, "13サービス", 70, 70)
    title_block(d, 70, 150, [("配信", PINK), ("サービス別", WHITE)], [("アニメランキング", WHITE)],
                "Netflix・Prime Video・U-NEXT・ABEMAなど", "サービスごとの人気アニメ", size=78)
    f = font(FONT_M, 23)
    x0, y, x = 750, 60, 750
    for i, s in enumerate(SERVICES):
        w = tw(d, s, f) + 36
        if x + w > 1160:
            x = x0; y += 62
        d.rounded_rectangle([x, y, x + w, y + 46], radius=10, fill=(30, 33, 44, 235), outline=(255, 255, 255, 110), width=2)
        d.text((x + 18, y + 9), s, font=f, fill=WHITE)
        x += w + 12
    # 再生ボタン
    px, py, pr = 1080, 520, 44
    d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=PINK + (230,), width=5)
    d.polygon([(px - 13, py - 21), (px - 13, py + 21), (px + 23, py)], fill=PINK + (230,))
    footer(d)
    save(img, "services")


# ---- netflix: 順位表（文字と図形だけ。ロゴは描かない） ----
def make_netflix():
    img, d = background(5, [(150, 120, 260, (110, 30, 50)), (1080, 520, 300, (110, 80, 30)), (980, 90, 200, (70, 30, 60))])
    badge(d, "公式Top10", 70, 70)
    title_block(d, 70, 150, [("Netflix", PINK)], [("アニメランキング", WHITE)],
                "Netflix公式の再生回数でわかる", "世界と日本で人気のアニメ", size=80)
    fh = font(FONT_M, 26); fn = font(FONT_B, 30)
    for j, (head, x) in enumerate((("世界", 740), ("日本", 960))):
        d.rounded_rectangle([x, 70, x + 200, 500], radius=16, fill=(30, 33, 44, 235), outline=PINK + (150,), width=2)
        d.text((x + 100 - tw(d, head, fh) // 2, 88), head, font=fh, fill=GOLD)
        for i in range(5):
            y = 145 + i * 68
            d.text((x + 22, y), str(i + 1), font=fn, fill=GOLD if i == 0 else WHITE)
            d.rounded_rectangle([x + 62, y + 10, x + 62 + (110 - i * 14), y + 30], radius=8, fill=PINK + (220 - i * 25,))
    footer(d)
    save(img, "netflix")


# ---- now-japan: 上がる棒グラフ ----
def make_now_japan():
    img, d = background(6, [(150, 120, 260, (120, 40, 90)), (1080, 520, 300, (110, 80, 30)), (900, 120, 220, (40, 60, 120))])
    badge(d, "毎月更新", 70, 70)
    title_block(d, 70, 150, [("国内", PINK), ("いま人気", WHITE)], [("アニメTOP30", WHITE)],
                "Netflix・U-NEXT・dアニメストアなど", "国内の配信ランキングを合算")
    bars(d, 770, 500, [90, 140, 190, 250, 320, 390], gap=62, bw=44)
    d.line([(760, 420), (1110, 120)], fill=GOLD + (220,), width=6)
    d.polygon([(1110, 120), (1072, 128), (1100, 158)], fill=GOLD + (230,))
    # 王冠
    cx, cy = 1110, 70
    crown = [(cx - 40, cy + 20), (cx - 40, cy - 14), (cx - 20, cy + 4), (cx, cy - 26), (cx + 20, cy + 4), (cx + 40, cy - 14), (cx + 40, cy + 20)]
    d.polygon(crown, fill=GOLD + (230,))
    footer(d)
    save(img, "now-japan")


# ---- season-2026-fall: 落ち葉の形（図形だけ） ----
def make_season_fall():
    img, d = background(7, [(150, 120, 260, (120, 50, 30)), (1080, 480, 320, (110, 70, 20)), (980, 90, 200, (90, 40, 70))])
    badge(d, "2026年秋", 70, 70, col=ORANGE)
    title_block(d, 70, 150, [("今季", PINK), ("アニメ", WHITE)], [("人気ランキング", WHITE)],
                "今期スタートの新作アニメを", "世界の注目度順にTOP30で紹介")
    random.seed(77)
    leaf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _ in range(26):
        x, y = random.randint(700, 1170), random.randint(40, 540)
        s = random.randint(18, 42)
        c = random.choice([ORANGE, GOLD, (230, 90, 60), PINK])
        one = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
        od = ImageDraw.Draw(one)
        od.ellipse([s * 0.5, s * 1.1, s * 2.5, s * 1.9], fill=c + (random.randint(150, 230),))
        od.line([(s * 0.4, s * 1.5), (s * 2.6, s * 1.5)], fill=(60, 30, 20, 160), width=2)
        one = one.rotate(random.randint(0, 180), resample=Image.BICUBIC)
        leaf.alpha_composite(one, (x - s, y - s))
    img.paste(leaf, (0, 0), leaf)
    d = ImageDraw.Draw(img, "RGBA")
    footer(d)
    save(img, "season-2026-fall")


if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    for fn in (make_year, make_country, make_genre, make_services, make_netflix, make_now_japan, make_season_fall):
        fn()
