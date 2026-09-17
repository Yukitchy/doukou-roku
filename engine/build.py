#!/usr/bin/env python3
"""同行録ビルダー: packs/<name>/pack.json + partN.json + audio/ → packs/<name>/index.html
使い方: python3 engine/build.py packs/<name>
"""
import json, sys, html, pathlib, re

pack = pathlib.Path(sys.argv[1]).resolve()
meta = json.loads((pack / "pack.json").read_text())
parts = []
for p_ in meta["parts"]:
    j = pack / p_["json"]
    d = json.loads(j.read_text()) if j.exists() else {"blurb": "（作成中）"}
    parts.append({**p_, **d})
tpl = (pathlib.Path(__file__).parent / "template.html").read_text()

E = html.escape
def mmss(s):
    s = int(s or 0); return f"{s//60:02d}:{s%60:02d}"
def inline(t):
    t = E(t)
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
def li(items, fmt=lambda x: inline(x)):
    return "".join(f"<li>{fmt(x)}</li>" for x in items) if items else "<li class='none'>なし</li>"
def ts(file, sec):
    return f"<a class='ts' href='#' data-file='{E(file)}' data-sec='{int(sec)}'>{mmss(sec)}</a>"

out = []
nav = []
for p in parts:
    pid = p["id"]; nav.append(f"<a href='#{pid}'>{E(p['title'])}</a>")
    audios = "".join(
        f"<div class='track'><span class='tname'>{E(a['label'])}</span>"
        f"<audio controls preload='none' data-file='{E(a['file'])}' src='audio/{E(a['file'])}'></audio></div>"
        for a in p["audio"])
    m = p.get("minutes", {})
    minutes = f"""
      <h3>議事録</h3>
      <p class='lead'>{inline(m.get('summary',''))}</p>
      <h4>話したこと</h4><ul>{li(m.get('topics',[]))}</ul>
      <h4>決まったこと・分かったこと</h4><ul>{li(m.get('decisions',[]))}</ul>
      <h4>決まっていないこと</h4><ul>{li(m.get('open',[]))}</ul>"""
    chapters = ""
    for c in p.get("chapters", []):
        lines = "".join(
            f"<div class='bubble'><div class='who'>{E(l.get('who',''))}<span class='t'>{ts(l['file'], l['t'])}</span></div>"
            f"<div class='say'>{inline(l['text'])}</div></div>" for l in c.get("lines", []))
        chapters += f"<section class='ch'><h4>{E(c['title'])}</h4><blockquote>{inline(c.get('lead',''))}</blockquote>{lines}</section>"
    hl = "".join(
        f"<li>{ts(h['file'], h['t'])} <q>{inline(h['quote'])}</q><span class='why'>{inline(h.get('why',''))}</span></li>"
        for h in p.get("highlights", []))
    prompts = "".join(
        f"<div class='prompt'><div class='phead'><b>{E(q['title'])}</b><span class='puse'>{inline(q.get('use',''))}</span>"
        f"<button class='copy' data-copy='{E(q['body'])}'>コピー</button></div><pre>{E(q['body'])}</pre></div>"
        for q in p.get("prompts", []))
    todos = "".join(
        f"<li><label><input type='checkbox' data-key='{pid}-{i}'> <b>{E(t.get('who',''))}</b> {inline(t['text'])}"
        f"{' <span class=due>'+E(t['due'])+'</span>' if t.get('due') else ''}</label></li>"
        for i, t in enumerate(p.get("todos", [])))
    links = "".join(f"<li><a href='{E(l['url'])}' target='_blank' rel='noopener'>{E(l['label'])}</a> <span class='why'>{inline(l.get('note',''))}</span></li>"
                    for l in p.get("links", []))
    out.append(f"""
<section class='part' id='{pid}'>
  <header><span class='ptime'>{E(p.get('time',''))}</span><h2>{E(p['title'])}</h2><p class='blurb'>{inline(p.get('blurb',''))}</p></header>
  <div class='tracks'>{audios}</div>
  <div class='block'>{minutes}</div>
  <div class='block'><h3>ハイライト</h3><ul class='hl'>{hl or "<li class='none'>なし</li>"}</ul></div>
  <div class='block'><h3>読み物</h3>{chapters}</div>
  <div class='block'><h3>AIプロンプト集</h3>{prompts or "<p class='none'>なし</p>"}</div>
  <div class='block'><h3>Todo</h3><ul class='todo'>{todos or "<li class='none'>なし</li>"}</ul></div>
  <div class='block'><h3>出てきた資料・ツール</h3><ul class='links'>{links or "<li class='none'>なし</li>"}</ul></div>
</section>""")

page = (tpl.replace("{{TITLE}}", E(meta["title"])).replace("{{DATE}}", E(meta.get("date","")))
        .replace("{{SUB}}", E(meta.get("subtitle",""))).replace("{{NAV}}", "".join(nav)).replace("{{BODY}}", "".join(out)))
(pack / "index.html").write_text(page)
print("wrote", pack / "index.html")
