#!/usr/bin/env python3
"""whisper json → [MM:SS] 行のテキスト。連続重複・文字連打（幻聴ループ）を落とす"""
import json, sys, re
d = json.load(open(sys.argv[1]))
prev = None; out = []
for s in d["segments"]:
    t = s["text"].strip()
    if not t or t == prev: continue
    if re.search(r"(.{1,4})\1{4,}", t): continue        # 「うんうんうん…」「!!!!」
    if s.get("compression_ratio", 0) > 2.4: continue
    prev = t
    out.append(f"[{int(s['start'])//60:02d}:{int(s['start'])%60:02d}] {t}")
print("\n".join(out))
