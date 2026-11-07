// ABEMA・DMM TV の検索結果を、サイトの全作品について隠れた枠で読み取る（2026-11-07 ユーザー「毎月全作品確認して正しい配信サービスボタンを配置する」）。
// abema.tv のタブで window.__SV='abema'、tv.dmm.com のタブで window.__SV='dmm' にしてから実行する。
// 終わると window.__svout に「作品キー<TAB>作品ページID<TAB>見つかった作品名」の行（一致したものだけ）、window.__svdone=true が入る。
(async () => {
  const SV = window.__SV; window.__svdone = false; window.__svout = ''; window.__svprog = 0;
  const idx = await (await fetch('https://raw.githubusercontent.com/masabee1029/anime-oshi-ranking/main/titles_index.json?' + Date.now())).json();
  const norm = t => (t || '').normalize('NFKC').replace(/[\s:：・!！?？\-－~～「」『』()（）【】\[\]〈〉.,、。'’"”/／★☆♪&＆]/g, '').toLowerCase();
  const strip = t => (t || '').replace(/[【\[（(「『].*?[】\]）)」』]/g, ' ').replace(/(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*[0-9０-９]+|シーズン\s*[0-9０-９]+|劇場版|総集編)/gi, ' ').replace(/\s*[0-9０-９]{1,2}$/, '').trim();
  const sel = SV === 'abema' ? 'a[href*="/video/title/"]' : 'a[href*="season="]';
  const idOf = h => SV === 'abema' ? (h.match(/title\/([0-9a-z_-]+)/) || [])[1] : (h.match(/season=([a-z0-9]+)/) || [])[1];
  const nameOf = x => SV === 'abema' ? (x.innerText.trim() || (x.querySelector('img') || {}).alt || '') : ((x.querySelector('img') || {}).alt || '').replace(/のサムネイル画像$/, '');
  const url = q => SV === 'abema' ? 'https://abema.tv/search?q=' + encodeURIComponent(q) : 'https://tv.dmm.com/vod/list/?keyword=' + encodeURIComponent(q);
  const SEASON = /^(第?[0-9一二三四五六七八九十]+(期|章|クール|シーズン|部)?|season[0-9]+|[0-9]+(st|nd|rd|th)season|part[0-9]+|ⅱ|ⅲ|ⅳ|ⅴ|ii|iii|iv|総集編|劇場版|前編|後編|新章|final(season)?|thefinalseason|ノ章|参ノ章|弐ノ章|[゜°'])+$/;
  const out = [];
  for (const it of idx.slice(window.__svstart || 0)) {
    window.__svprog++;
    const q = strip(it.title) || it.title; const want = [it.title, ...(it.alts || [])].map(norm).concat([norm(q)]).filter(Boolean);
    const f = document.createElement('iframe'); f.style.cssText = 'width:1200px;height:900px;position:fixed;left:-3000px'; f.src = url(q); document.body.appendChild(f);
    let got = null;
    for (let i = 0; i < 8; i++) { await new Promise(r => setTimeout(r, 1000));
      let as = []; try { as = [...f.contentDocument.querySelectorAll(sel)]; } catch (e) { break; }
      if (!as.length) continue;
      await new Promise(r => setTimeout(r, 800)); as = [...f.contentDocument.querySelectorAll(sel)];
      for (const x of as) { const n = norm(nameOf(x)); const id = idOf(x.getAttribute('href') || ''); if (!n || !id) continue;
        // 名前が同じか、違いが「第2期」「Season2」「総集編」のような続き物の印だけのときに同じ作品とみなす（「攻殻機動隊」と「攻殻機動隊ARISE」は別）
        const ok = want.some(w => { if (w === n) return true; const [a, b] = w.length < n.length ? [w, n] : [n, w];
          return a.length >= 4 && b.startsWith(a) && SEASON.test(b.slice(a.length)); });
        if (ok) { got = [id, nameOf(x).slice(0, 60)]; break; } }
      break; }
    f.remove();
    if (got) out.push(it.key + '\t' + got[0] + '\t' + got[1]);
    window.__svout = out.join('\n');
  }
  window.__svdone = true;
})();
