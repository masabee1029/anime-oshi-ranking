// ABEMA の作品ページを 1 つずつ隠れた枠で開き、エピソードのリンクの数を数える（abema.tv のタブで実行）。
// 使い方: window.__AB_URLS = [...]; この中身を実行 → 数分後に window.__abres を読む（{url: 本数}。0 = 配信なし、-2 = 読めない）
(async () => { const res = {}; window.__abres = null;
 for (const u of window.__AB_URLS) { const f = document.createElement('iframe'); f.style.cssText = 'width:1200px;height:900px;position:fixed;left:-3000px'; f.src = u; document.body.appendChild(f);
  let n = 0; for (let i = 0; i < 20; i++) { await new Promise(r => setTimeout(r, 1000)); try { n = f.contentDocument.querySelectorAll('a[href*="/video/episode/"]').length; if (n > 0) break; } catch (e) { n = -2; break; } }
  res[u] = n; f.remove(); }
 window.__abres = res; })();
