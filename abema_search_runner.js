// ABEMA の検索（ABEMA の画面が使っている検索 API）で、サイトの全作品を数分で調べる（2026-11-07）。abema.tv のタブで実行する。
// ログイン中のトークンは画面・ログ・ファイルに出さない。終わると window.__svout に「作品キー<TAB>作品ID<TAB>ABEMA の作品名」、window.__svdone=true。
(async () => {
  window.__svdone = false; window.__svout = ''; window.__svprog = 0; window.__sverr = 0;
  const idx = await (await fetch('https://raw.githubusercontent.com/masabee1029/anime-oshi-ranking/main/titles_index.json?' + Date.now())).json();
  const norm = t => (t || '').normalize('NFKC').replace(/[\s:：・!！?？\-－~～「」『』()（）【】\[\]〈〉.,、。'’"”/／★☆♪&＆]/g, '').toLowerCase();
  const strip = t => (t || '').replace(/[【\[（(「『].*?[】\]）)」』]/g, ' ').replace(/(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*[0-9０-９]+|シーズン\s*[0-9０-９]+|劇場版|総集編)/gi, ' ').replace(/\s*[0-9０-９]{1,2}$/, '').trim();
  const SEASON = /^(第?[0-9一二三四五六七八九十]+(期|章|クール|シーズン|部)?|season[0-9]+|[0-9]+(st|nd|rd|th)season|part[0-9]+|ⅱ|ⅲ|ⅳ|ⅴ|ii|iii|iv|総集編|劇場版|前編|後編|新章|final(season)?|thefinalseason|ノ章|参ノ章|弐ノ章|[゜°'])+$/;
  const H = {headers: {Authorization: 'bearer ' + localStorage.getItem('abm_token')}};
  const same = (want, n) => want.some(w => { if (w === n) return true; const [a, b] = w.length < n.length ? [w, n] : [n, w];
    return a.length >= 4 && b.startsWith(a) && SEASON.test(b.slice(a.length)); });
  const out = [];
  for (const it of idx) {
    window.__svprog++;
    const q = strip(it.title) || it.title; const want = [it.title, ...(it.alts || [])].map(norm).concat([norm(q)]).filter(Boolean);
    let j = null;
    for (let t = 0; t < 3 && !j; t++) { try { const r = await fetch('https://api.p-c3-e.abema-tv.com/v1/search/modules?query=' + encodeURIComponent(q) + '&device=WEB&itemLimit=8', H); if (r.ok) j = await r.json(); } catch (e) {} if (!j) await new Promise(r => setTimeout(r, 2000)); }
    if (!j) { window.__sverr++; continue; }
    const res = [];
    for (const m of j.modules || []) for (const x of (((m.items || {}).content || {}).results || [])) { const vs = (x.contentData || {}).videoSeries; if (vs && vs.title) res.push([x.contentId, vs.title]); }
    const hit = res.find(([id, t]) => same(want, norm(t)));
    if (hit) out.push(it.key + '\t' + hit[0] + '\t' + hit[1].slice(0, 60));
    window.__svout = out.join('\n');
    await new Promise(r => setTimeout(r, 300));
  }
  window.__svdone = true;
})();
