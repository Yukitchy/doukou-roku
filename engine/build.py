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
    hide = p_.pop("hide", [])
    parts.append({**p_, **d, "hide": hide})

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

    blocks = []
    if p.get("photos"):
        ph = "".join(f"<figure><img loading='lazy' src='{E(x['file'])}' alt='{E(x.get('caption',''))}'>"
                     f"<figcaption>{E(x.get('caption',''))}</figcaption></figure>" for x in p["photos"])
        blocks.append(f"<div class='photos'>{ph}</div>")
    blocks.append(sec_block(f"音声 {len(p['audio'])}本", f"<div class='tracks'>{tracks}</div>"))

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

    if p.get("prompts") and "prompts" not in p["hide"]:
        pr = "".join(
            f"<details class='prompt'><summary><div class='phead'><h4>{E(q['title'])}</h4>"
            f"<button class='copy' data-copy=\"{E(q['body'])}\">コピー</button>"
            f"<p class='puse'>{inline(q.get('use',''))}</p></div></summary>"
            f"<pre>{E(q['body'])}</pre></details>"
            for q in p["prompts"])
        blocks.append(sec_block("AIプロンプト集 — コピーして貼るだけ", pr, foldable=True))

    if p.get("todos") and "todos" not in p["hide"]:
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
# 「次の回の種」: pack.json の seeds[] を最後に1枚のボードとして出す（無ければ空）
seeds = ""
if not meta.get("seeds"):  # auto-collect seeds from parts
    meta["seeds"] = [dict(sd, part=q["id"]) for q in parts for sd in q.get("seeds", [])]
if meta.get("seeds"):
    cards = ""
    for i, sd in enumerate(meta["seeds"]):
        part = next((q for q in parts if q["id"] == sd.get("part")), None)
        play = ts(part, sd["file"], sd["t"], mmss(sd["t"]) + " から聴く") if part and sd.get("file") else ""
        cards += (f"<li class='seed'><div class='sno'>{i+1:02d}</div><div>"
                  f"<h4>{E(sd['title'])}</h4><p class='sq'>{inline(sd.get('quote',''))}"
                  f"<span class='swho'>— {E(sd.get('who',''))}</span> {play}</p>"
                  f"<p class='swhy'>{inline(sd.get('why',''))}</p>"
                  + (f"<p class='snext'><b>次の一手</b> {inline(sd['next'])}</p>" if sd.get('next') else '')
                  + "</div></li>")
    seeds = (f"<div class='part seeds' id='seeds'><header><div class='ptime'>{E(meta.get('seeds_eyebrow',''))}</div>"
             f"<h2>{E(meta.get('seeds_title','ここから生まれる次の回'))}</h2>"
             f"<p class='blurb'>{inline(meta.get('seeds_lead',''))}</p></header><ol class='seedlist'>{cards}</ol></div>")
    nav.append("<a href='#seeds'>次の回の種<small></small></a>")
resources = ""
if meta.get("resources"):
    cards = "".join(
        f"<a class='res' href='{E(r['url'])}' target='_blank' rel='noopener'>"
        + (f"<img loading='lazy' src='{E(r['image'])}' alt=''>" if r.get("image") else "<div class='noimg'></div>")
        + f"<div><b>{E(r['label'])}</b><span>{E(r.get('note',''))}</span></div></a>" for r in meta["resources"])
    resources = (f"<div class='part' id='resources'><header><div class='ptime'>話に出た場所・団体・出来事</div>"
                 f"<h2>{E(meta.get('resources_title','関連リンク'))}</h2>"
                 f"<p class='blurb'>{inline(meta.get('resources_lead',''))}</p></header><div class='resgrid'>{cards}</div></div>")
    nav.append("<a href='#resources'>関連リンク<small></small></a>")
page = page.replace("{{NAV}}", "".join(nav))
sticky = "".join(f"<a href='#{p['id']}'>{E(p['title'])}</a>" for p in parts)
hero = meta.get("hero")
page = page.replace("{{HERO}}", f"<figure class='hero'><img src='{E(hero['file'])}' alt='{E(hero.get('caption',''))}'><figcaption>{E(hero.get('caption',''))}</figcaption></figure>" if hero else "")
page = page.replace("{{STICKY}}", sticky).replace("{{BODY}}", "".join(body) + seeds + resources)
(pack / "index.html").write_text(page)
print("wrote", pack / "index.html")
