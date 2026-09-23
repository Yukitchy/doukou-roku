#!/usr/bin/env python3
"""Inline the 3 language JSONs into template.html -> index.html, and render transcript.html."""
import json, re, html, pathlib, sys
here = pathlib.Path(__file__).parent
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here
out.mkdir(parents=True, exist_ok=True)

data = {k: json.load(open(here / f"data.{k}.json")) for k in ("ja", "en", "zh")}
tpl = (here / "template.html").read_text()
page = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
(out / "index.html").write_text(page)

# transcript
md = (here / "transcripts" / "02.md").read_text().splitlines()
rows = []
for ln in md:
    m = re.match(r"\*\*(.+?)\*\* \[(\d+:\d\d)\] (.*)", ln)
    if not m:
        continue
    who, t, txt = m.groups()
    cls = {"Yuki": "y", "Stevo": "s", "Erika": "e"}.get(who, "q")
    rows.append(f'<p class="{cls}"><b>{html.escape(who)}</b><span class="t">{t}</span>{html.escape(txt)}</p>')

transcript = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Transcript · Akihabara Meeting 2026.09.23</title>
<style>
:root{{--accent:#B8322A;--ink:#1F2426;--sub:#5F6B6E;--line:#DDD8CF;--bg:#FBF8F3;--band:#F1ECE3}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:820px;margin:0 auto;padding:32px 20px 80px}}
h1{{font-size:24px;margin:0 0 6px}} .sub{{color:var(--sub);margin:0 0 18px;font-size:15px}}
.note{{background:var(--band);border-radius:12px;padding:12px 16px;font-size:14px;margin:0 0 28px}}
.note p{{margin:4px 0}}
p.y,p.s,p.e,p.q{{margin:0;padding:8px 0;border-top:1px solid var(--line);display:grid;grid-template-columns:5.2em 3.4em 1fr;gap:8px;font-size:15px}}
p b{{font-weight:700}} p.y b{{color:var(--accent)}} p.s b{{color:#1F5F8B}} p.e b{{color:#6B4C9A}} p.q b{{color:var(--sub)}}
.t{{color:var(--sub);font-variant-numeric:tabular-nums;font-size:13px;padding-top:2px}}
a{{color:var(--accent)}}
@media(max-width:600px){{p.y,p.s,p.e,p.q{{grid-template-columns:4.6em 3em 1fr;gap:6px;font-size:14px}}}}
</style></head><body><div class="wrap">
<p><a href="index.html">Notes / まとめへ戻る / 返回摘要</a></p>
<h1>Transcript</h1>
<p class="sub">Recording 2: LUUP JR秋葉原駅電気街口.m4a (31:59), 2026-09-23, Akihabara</p>
<div class="note">
<p>Speakers were identified from context (no automatic diarization). "?" means unsure. [不明瞭] marks parts that could not be heard clearly. Text is the raw transcript; nothing was added.</p>
<p>話者は内容から推定（機械分離なし）。「?」は判定できなかった発言、［不明瞭］は聞き取れなかった箇所。原文のまま、加筆なし。</p>
<p>發言者由內容推斷（無自動分離）。「?」為無法判斷的發言，［不明瞭］為聽不清楚的部分。原文照錄，未有增刪。</p>
<p>Recording 1 (新規録音 13.m4a, 13:12) was almost silent throughout (about -55 dB) and could not be transcribed. ／ 録音1は全体がほぼ無音で文字起こし不能でした。／ 錄音1全程幾乎無聲，無法轉寫。</p>
</div>
{chr(10).join(rows)}
</div></body></html>"""
(out / "transcript.html").write_text(transcript)
print("built", out / "index.html", len(page), "bytes;", len(rows), "transcript rows")
