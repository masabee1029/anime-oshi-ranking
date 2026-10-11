# 推しアニメランキング

GitHub Pages で公開しているアニメおすすめ・ランキングサイト。
データ元は `~/knowledge-os/raw/anime`（毎月1日 07:00 に自動更新）。

## 更新手順
```
python3 build.py   # docs/ を再生成
git add -A && git commit -m "update" && git push
```

## アフィリエイト設定
`affiliate.json` に各 ASP の ID を入れて `python3 build.py` を実行すると全リンクが差し替わる。
- `amazon_tag`: Amazon アソシエイトのトラッキング ID（例: masabee-22）
- `rakuten_affiliate_id`: 楽天アフィリエイト ID
- `moshimo_unext_url` / `moshimo_dmmtv_url`: もしもアフィリエイトで発行した U-NEXT / DMM TV の紹介リンク
- `contact_url`: お問い合わせフォーム（Google フォーム等）の URL
