// TVer の全作品検索（2026-11-07）。tver.jp の検索ページ（例 https://tver.jp/search/アニメ）を開いたタブで実行する。
// ページ自身が読んだ検索 API の URL（匿名の利用者 ID 入り）を使い回し、キーワードだけ差し替える。ID は画面に出さない。
// 出力: window.__svout = 「作品キー<TAB>シリーズID<TAB>TVer の番組名<TAB>いちばん遅い配信期限（UNIX 秒）」→ svc_apply.py TVer
(async () => {
  window.__svdone = false; window.__svout = ''; window.__svprog = 0; window.__sverr = 0;
  const base = performance.getEntriesByType('resource').map(e => e.name).find(n => /callKeywordSearch/.test(n));
  if (!base) { window.__sverr = -1; window.__svdone = true; return; }
  const idx = await (await fetch('https://raw.githubusercontent.com/masabee1029/anime-oshi-ranking/main/titles_index.json?' + Date.now())).json();
  const norm = t => (t || '').normalize('NFKC').replace(/[\s:：・!！?？\-－~～「」『』()（）【】\[\]〈〉.,、。'’"”/／★☆♪&＆]/g, '').toLowerCase();
  const strip = t => (t || '').replace(/[【\[（(「『].*?[】\]）)」』]/g, ' ').replace(/(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*[0-9０-９]+|シーズン\s*[0-9０-９]+|劇場版|総集編)/gi, ' ').replace(/\s*[0-9０-９]{1,2}$/, '').trim();
  const SEASON = /^(第?([1-9][0-9]?|[一二三四五六七八九十]+)(期|章|クール|シーズン|部)?|season[1-9][0-9]?|[1-9][0-9]?(st|nd|rd|th)season|part[1-9]|ⅱ|ⅲ|ⅳ|ⅴ|ii|iii|iv|総集編|前編|後編|新章|final(season)?|thefinalseason|ノ章|参ノ章|弐ノ章|[゜°'])+$/;
  // TVer は放送中の話だけが観られるので、続き物の別シーズンには付けない。名前が同じか、シーズン番号まで同じ（第2期 = 2nd Season）ときだけ
  const SN = /(第([1-9][0-9]?)(期|シーズン)|([1-9][0-9]?)(st|nd|rd|th)season|season([1-9][0-9]?)|シーズン([1-9][0-9]?))$/;
  const split = t => { const m = t.match(SN); return m ? [t.slice(0, m.index), m.slice(2).find(x => /^[0-9]+$/.test(x || ''))] : [t, '']; };
  const same = (want, n) => want.some(w => { if (w === n) return true; const [a, x] = split(w), [b, y] = split(n); return x && x === y && a === b && a.length >= 2; });
  const now = Date.now() / 1000, out = [];
  for (const it of idx) {
    window.__svprog++;
    const q = strip(it.title) || it.title; const want = [it.title, ...(it.alts || [])].map(norm).concat([norm(q)]).filter(Boolean);
    const u = new URL(base); u.searchParams.set('keyword', q);
    let j = null;
    for (let t = 0; t < 3 && !j; t++) { try { const r = await fetch(u, {headers: {'x-tver-platform-type': 'web'}}); if (r.ok) j = await r.json(); } catch (e) {} if (!j) await new Promise(r => setTimeout(r, 2000)); }
    if (!j) { window.__sverr++; continue; }
    const by = {};
    for (const x of ((j.result || {}).contents || [])) { const c = x.content || {};
      if (x.type !== 'episode' || c.isAvailable === false || !c.seriesID || !(c.endAt > now)) continue;
      if (!same(want, norm(c.seriesTitle))) continue;
      const b = by[c.seriesID] || (by[c.seriesID] = {name: c.seriesTitle, end: 0, n: 0}); b.n++; b.end = Math.max(b.end, c.endAt); }
    const best = Object.entries(by).sort((a, b) => b[1].n - a[1].n)[0];
    if (best) out.push(it.key + '\t' + best[0] + '\t' + best[1].name.slice(0, 60) + '\t' + best[1].end);
    window.__svout = out.join('\n');
    await new Promise(r => setTimeout(r, 300));
  }
  window.__svdone = true;
})();
