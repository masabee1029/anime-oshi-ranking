// TVer の全作品検索（2026-11-07、2026-11-27 TVer の検索 API 変更に合わせて書き直し）。tver.jp の検索ページ（例 https://tver.jp/search/アニメ）を開いたタブで実行する。
// ページ自身が読んだ検索 API（contents-api …/page/search_result）の URL を使い回し、キーワードだけ差し替える。URL の中身は画面に出さない。
// 検索結果のエピソード（subtitle = 番組名）を名前で絞り、statics.tver.jp/content/episode/<id>.json から seriesID と配信期限（viewStatus.endAt）を取る。
// 出力: window.__svout = 「作品キー<TAB>シリーズID<TAB>TVer の番組名<TAB>いちばん遅い配信期限（UNIX 秒）」→ svc_apply.py TVer
(async () => {
  window.__svdone = false; window.__svout = ''; window.__svprog = 0; window.__sverr = 0;
  const base = performance.getEntriesByType('resource').map(e => e.name).find(n => /contents\/api\/v1\/page\/search_result/.test(n));
  if (!base) { window.__sverr = -1; window.__svdone = true; return; }
  const idx = await (await fetch('https://raw.githubusercontent.com/masabee1029/anime-oshi-ranking/main/titles_index.json?' + Date.now())).json();
  const norm = t => (t || '').normalize('NFKC').replace(/[\s:：・!！?？\-－~～「」『』()（）【】\[\]〈〉.,、。'’"”/／★☆♪&＆]/g, '').toLowerCase();
  const strip = t => (t || '').replace(/[【\[（(「『].*?[】\]）)」』]/g, ' ').replace(/(第\s*\d+\s*(期|章|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*[0-9０-９]+|シーズン\s*[0-9０-９]+|劇場版|総集編)/gi, ' ').replace(/\s*[0-9０-９]{1,2}$/, '').trim();
  // TVer は放送中の話だけが観られるので、続き物の別シーズンには付けない。名前が同じか、シーズン番号まで同じ（第2期 = 2nd Season）ときだけ
  const SN = /(第([1-9][0-9]?)(期|シーズン)|([1-9][0-9]?)(st|nd|rd|th)season|season([1-9][0-9]?)|シーズン([1-9][0-9]?))$/;
  const split = t => { const m = t.match(SN); return m ? [t.slice(0, m.index), m.slice(2).find(x => /^[0-9]+$/.test(x || ''))] : [t, '']; };
  const same = (want, n) => want.some(w => { if (w === n) return true; const [a, x] = split(w), [b, y] = split(n); return x && x === y && a === b && a.length >= 2; });
  const get = async (u, h) => { for (let t = 0; t < 3; t++) { try { const r = await fetch(u, h); if (r.ok) return await r.json(); } catch (e) {} await new Promise(r => setTimeout(r, 2000)); } return null; };
  const now = Date.now() / 1000, out = [];
  for (const it of idx) {
    window.__svprog++;
    const q = strip(it.title) || it.title; const want = [it.title, ...(it.alts || [])].map(norm).concat([norm(q)]).filter(Boolean);
    const u = new URL(base); u.searchParams.set('keyword', q);
    const j = await get(u, {headers: {'x-tver-platform-type': 'web'}});
    if (!j) { window.__sverr++; continue; }
    const eps = [];
    for (const s of ((j.floor || {}).sections || [])) for (const x of (s.items || [])) if (x.item_type === 'episode' && same(want, norm(x.subtitle))) eps.push(x);
    const by = {};
    for (const x of eps.slice(0, 15)) {
      const e = await get('https://statics.tver.jp/content/episode/' + x.id + '.json');
      if (!e) continue; const end = ((e.viewStatus || {}).endAt) || 0;
      if (!e.seriesID || !(end > now)) continue;
      const b = by[e.seriesID] || (by[e.seriesID] = {name: x.subtitle, end: 0, n: 0}); b.n++; b.end = Math.max(b.end, end);
    }
    const best = Object.entries(by).sort((a, b) => b[1].n - a[1].n)[0];
    if (best) out.push(it.key + '\t' + best[0] + '\t' + best[1].name.slice(0, 60) + '\t' + best[1].end);
    window.__svout = out.join('\n');
    await new Promise(r => setTimeout(r, 300));
  }
  window.__svdone = true;
})();
