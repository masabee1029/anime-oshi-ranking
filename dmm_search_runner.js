// DMM TV の検索（DMM TV の画面が使っている検索）で、サイトの全作品を数分で調べる（2026-11-07）。tv.dmm.com のタブで実行する。
// 見放題（PREMIUM）か無料（FREE）の作品だけを数える（PPV＝レンタル・購入は数えない）。
// 終わると window.__svout に「作品キー<TAB>作品ID（season）<TAB>DMM TV の作品名」、window.__svdone=true。
(async () => {
  window.__svdone = false; window.__svout = ''; window.__svprog = 0; window.__sverr = 0;
  const idx = await (await fetch('https://raw.githubusercontent.com/masabee1029/anime-oshi-ranking/main/titles_index.json?' + Date.now())).json();
  const norm = t => (t || '').normalize('NFKC').replace(/[\s:：・!！?？\-－~～「」『』()（）【】\[\]〈〉.,、。'’"”/／★☆♪&＆]/g, '').toLowerCase();
  const strip = t => (t || '').replace(/[【\[（(「『].*?[】\]）)」』]/g, ' ').replace(/(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*[0-9０-９]+|シーズン\s*[0-9０-９]+|劇場版|総集編)/gi, ' ').replace(/\s*[0-9０-９]{1,2}$/, '').trim();
  const SEASON = /^(第?([1-9][0-9]?|[一二三四五六七八九十]+)(期|章|クール|シーズン|部)?|season[0-9]+|[0-9]+(st|nd|rd|th)season|part[0-9]+|ⅱ|ⅲ|ⅳ|ⅴ|ii|iii|iv|総集編|前編|後編|新章|final(season)?|thefinalseason|ノ章|参ノ章|弐ノ章|[゜°'])+$/;
  const Q = 'query S($device: Device!, $keyword: String, $first: Int){searchVideos(device:$device, keyword:$keyword, first:$first){edges{node{id titleName seasonName viewingTypes}}}}';
  const same = (want, n) => want.some(w => { if (w === n) return true; const [a, b] = w.length < n.length ? [w, n] : [n, w];
    return a.length >= 4 && b.startsWith(a) && SEASON.test(b.slice(a.length)); });
  const out = [];
  for (const it of idx) {
    window.__svprog++;
    const q = strip(it.title) || it.title; const want = [it.title, ...(it.alts || [])].map(norm).concat([norm(q)]).filter(Boolean);
    let j = null;
    for (let t = 0; t < 3 && !j; t++) { try { const r = await fetch('https://api.tv.dmm.com/graphql', {method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({operationName: 'S', variables: {keyword: q, device: 'BROWSER', first: 20}, query: Q})}); if (r.ok) j = await r.json(); } catch (e) {} if (!j) await new Promise(r => setTimeout(r, 2000)); }
    if (!j) { window.__sverr++; continue; }
    const res = [];
    for (const e of ((((j.data || {}).searchVideos) || {}).edges || [])) { const n = e.node || {}; if (!(n.viewingTypes || []).some(v => v === 'PREMIUM' || v === 'FREE')) continue;
      const sn = n.seasonName || '', tn = n.titleName || '';
      const full = !sn || sn === tn ? tn : (norm(sn).startsWith(norm(tn)) ? sn : tn + ' ' + sn); res.push([n.id, full, tn, sn]); }
    // ① シーズン名まで同じ ② 続き物の印だけ違う ③ 作品名だけ同じ（DMM TV は 1 つの作品名に別シリーズをまとめるので、
    //    シーズン名が「シーズン1」「1年目」のような印のときだけ。「攻殻機動隊」と「…STAND ALONE COMPLEX」は別の作品として扱う）
    const base = s => !s || SEASON.test(norm(s)) || /^(第?[0-9一二三四五六七八九十]+年目|シーズン[0-9]+|season[0-9]+)$/i.test(norm(s));
    const hit = res.find(([id, f]) => want.includes(norm(f))) || res.find(([id, f]) => same(want, norm(f)))
      || res.find(([id, f, t, sn]) => (same(want, norm(t)) && (sn === t || base(sn))) || (want.some(w => w !== norm(t) && w.startsWith(norm(t)) && SEASON.test(w.slice(norm(t).length))) && same(want, norm(t))));
    if (hit) out.push(it.key + '\t' + hit[0] + '\t' + hit[1].slice(0, 60));
    window.__svout = out.join('\n');
    await new Promise(r => setTimeout(r, 300));
  }
  window.__svdone = true;
})();
