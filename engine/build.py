#!/usr/bin/env python3
"""同行録ビルダー: packs/<name>/pack.json + partN.json + audio/ → packs/<name>/index.html
使い方: python3 engine/build.py packs/<name>
"""
import json, sys, html, pathlib, re

pack = pathlib.Path(sys.argv[1]).resolve()
meta = json.loads((pack / "pack.json").read_text())
tpl = (pathlib.Path(__file__).parent / "template.html").read_text()

parts = []
for p_ in meta["parts"]:
    j = pack / p_["json"]
    d = json.loads(j.read_text()) if j.exists() else {}
    parts.append({**p_, **d})

E = html.escape
def mmss(s):
    s = int(s or 0)
    return f"{s//60}:{s%60:02d}" if s < 3600 else f"{s//3600}:{s//60%60:02d}:{s%60:02d}"
def inline(t):
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", E(t or ""))
def label_of(part, f):
    for a in part["audio"]:
        if a["file"] == f: return a["label"]
    return f
def ts(part, f, sec, text=None):
    return (f"<a class='ts' href='#' data-file=\"{E(f)}\" data-sec='{int(sec)}' "
            f"data-label=\"{E(label_of(part, f))}\">{text or mmss(sec)}</a>")

def sec_block(title, inner, foldable=False):
    btn = "<button class='openall' type='button'>すべて開く</button>" if foldable else ""
    return f"<section class='blk'><h3>{title}{btn}</h3>{inner}</section>"

body, nav = [], []
for p in parts:
    pid, m = p["id"], p.get("minutes", {})
    nav.append(f"<a href='#{pid}'>{E(p['title'])}<small>{E(p.get('time',''))}</small></a>")

    tracks = "".join(
        f"<div class='track'><div class='tname'>{E(a['label'])}</div>"
        f"<audio controls preload='none' src='audio/{E(a['file'])}'></audio></div>"
        for a in p["audio"])

    blocks = [sec_block(f"音声 {len(p['audio'])}本", f"<div class='tracks'>{tracks}</div>")]

    if m.get("summary"):
        topics = "".join(f"<li>{inline(t)}</li>" for t in m.get("topics", []))
        blocks.append(sec_block("議事録",
            f"<p class='summary'>{inline(m['summary'])}</p>"
            + (f"<details class='fold'><summary>話したこと <span class='cnt'>{len(m['topics'])}件</span></summary>"
               f"<ul class='tl'>{topics}</ul></details>" if topics else "")))

    if m.get("decisions"):
        items = "".join(f"<li><div class='num'>{i+1}</div><div><b>{inline(d)}</b></div></li>"
                        for i, d in enumerate(m["decisions"]))
        blocks.append(f"<section class='blk'><div class='band'><h3>決まったこと・分かったこと</h3><ol>{items}</ol></div></section>")

    if m.get("open"):
        rows = "".join(f"<div><span>?</span><div>{inline(o)}</div></div>" for o in m["open"])
        blocks.append(sec_block("決まっていないこと", f"<div class='open'>{rows}</div>"))

    if p.get("highlights"):
        qs = "".join(
            f"<li><blockquote>{inline(h['quote'])}</blockquote>"
            f"<div class='qm'><span class='why'>{inline(h.get('why',''))}</span>"
            f"{ts(p, h['file'], h['t'], mmss(h['t']) + ' から聴く')}</div></li>"
            for h in p["highlights"])
        blocks.append(sec_block("ハイライト", f"<ul class='quotes'>{qs}</ul>"))

    if p.get("chapters"):
        chs = ""
        for c in p["chapters"]:
            lines = "".join(
                f"<div class='say'><div class='who'>{E(l.get('who','—'))}"
                f"<span class='t'>{ts(p, l['file'], l['t'])}</span></div>"
                f"<p>{inline(l['text'])}</p></div>" for l in c.get("lines", []))
            chs += (f"<details class='ch'><summary><h4>{E(c['title'])}</h4>"
                    f"<div class='chlead'>{inline(c.get('lead',''))}</div>"
                    f"<span class='cnt'>{len(c.get('lines', []))}発言</span></summary>"
                    f"<div class='lines'>{lines}</div></details>")
        blocks.append(sec_block("読み物", chs, foldable=True))

    if p.get("prompts"):
        pr = "".join(
            f"<details class='prompt'><summary><div class='phead'><h4>{E(q['title'])}</h4>"
            f"<button class='copy' data-copy=\"{E(q['body'])}\">コピー</button>"
            f"<p class='puse'>{inline(q.get('use',''))}</p></div></summary>"
            f"<pre>{E(q['body'])}</pre></details>"
            for q in p["prompts"])
        blocks.append(sec_block("AIプロンプト集 — コピーして貼るだけ", pr, foldable=True))

    if p.get("todos"):
        rows = "".join(
            f"<div><b>{E(t.get('who','—'))}</b><label><input type='checkbox' data-key='{pid}-{i}'>"
            f"<span>{inline(t['text'])}" + (f"<span class='due'>{E(t['due'])}</span>" if t.get('due') else '') + "</span></label></div>"
            for i, t in enumerate(p["todos"]))
        blocks.append(sec_block("Todo", f"<div class='hw'>{rows}</div>"))

    if p.get("links"):
        rows = "".join(
            "<li><b>" + (f"<a href='{E(l['url'])}' target='_blank' rel='noopener'>{E(l['label'])}</a>"
                         if l.get("url") else E(l["label"]))
            + f"</b><span class='why'>{inline(l.get('note',''))}</span></li>" for l in p["links"])
        blocks.append(sec_block("出てきた資料・ツール",
            f"<details class='fold'><summary>会話に出たもの <span class='cnt'>{len(p['links'])}件</span></summary>"
            f"<ul class='links'>{rows}</ul></details>"))

    body.append(f"""<div class='part' id='{pid}'>
  <header><div class='ptime'>{E(p.get('time',''))}</div><h2>{E(p['title'])}</h2>
  <p class='blurb'>{inline(p.get('blurb',''))}</p></header>
  {''.join(blocks)}
</div>""")

page = tpl
for k, v in {"TITLE": meta["title"], "BRAND": meta.get("brand", meta["title"]),
             "DATE": meta.get("date", ""), "EYEBROW": meta.get("eyebrow", ""),
             "H1": meta.get("h1", meta["title"]), "LEAD": meta.get("lead", ""),
             "NOTE": meta.get("note", "")}.items():
    page = page.replace("{{" + k + "}}", E(v).replace("\n", "<br>") if k == "H1" else E(v))
page = page.replace("{{NAV}}", "".join(nav))
sticky = "".join(f"<a href='#{p['id']}'>{E(p['title'])}</a>" for p in parts)
page = page.replace("{{STICKY}}", sticky).replace("{{BODY}}", "".join(body))
(pack / "index.html").write_text(page)
print("wrote", pack / "index.html")
