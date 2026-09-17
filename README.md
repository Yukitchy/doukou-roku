# 同行録（doukou-roku）

一日ぶんの録音（複数ファイル）を「部」に分けて、議事録・ハイライト・読み物・AIプロンプト集・Todo・出てきた資料 を1ページにする箱。
**engine/ が仕組み、packs/<名前>/ が中身**。

## 使い方
1. `packs/<名前>/audio/` に音声を置き、`pack.json` に部ごとの音声リスト（label/file）を書く
2. 文字起こし: `mlx_whisper <音声> --model mlx-community/whisper-large-v3-turbo --language ja --output-format json --condition-on-previous-text False` → `python3 engine/seg2md.py <json> > transcripts/NN.md`（`--condition-on-previous-text False` は必須。付けないと「うんうん…」の幻聴ループで後半が消える）
3. 各部の要約: `engine/part_prompt.md` を指示書に、文字起こしを書記（Claude）へ渡して `partN.json` を書かせる
4. `python3 engine/build.py packs/<名前>` → `packs/<名前>/index.html`（Chromeで file:// のまま開ける・時刻クリックで該当箇所を再生）

## pack.json
```json
{"title":"…","date":"…","subtitle":"…",
 "parts":[{"id":"pre","title":"ツアー前mtg","json":"part1.json","audio":[{"label":"12:13 住吉","file":"xxx.m4a"}]}]}
```
