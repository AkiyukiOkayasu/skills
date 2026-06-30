---
name: gndless-pdf
description: Use when you need to inspect a local PDF or a PDF found on the web, extract only the relevant pages or elements, or render page images for visually dense PDFs such as schematics, diagrams, and scanned drawings while keeping context usage low.
---

# Gndless PDF

`opendataloader-pdf` を前処理に使い、必要なページや要素だけを reasoning に渡す。  
文字主体の PDF は抽出、回路図や図面のような視覚主体の PDF は画像化を優先する。

## 使う場面

- user guide、datasheet、仕様書、論文などの特定ページだけ見たい
- Web で見つけた PDF をいったんローカル化してから絞り込みたい
- 回路図、配線図、ブロック図、スキャン資料のように画像として見た方がよい
- PDF 全文をコンテキストに積みたくない

## 基本方針

- まず `inspect` でページ数やメタ情報を確認する
- 文字主体の PDF は `extract` で必要ページをまとめて抽出する
- 視覚主体の PDF は `render` で対象ページを PNG 化して読む
- 回答に使うのは JSON / Markdown / 画像のうち必要部分だけ
- 根拠が必要なときは page number と bounding box を維持する

## 文字主体か視覚主体かの目安

- datasheet、manual、論文、表中心なら `extract`
- 回路図、PCB 図、タイミング図、注釈の細かい図面なら `render`
- OCR 品質が悪くテキスト抽出が崩れる PDF も `render` を優先する

## ツール

- 実体は `scripts/pdf_selective_ingest.py`
- 変換バックエンドは `opendataloader-pdf`
- ローカル PDF と HTTP/HTTPS の PDF URL を両方受けられる
- `inspect` は `pdfinfo`、`render` は `pdftoppm` を使う
- `pdfinfo` と `pdftoppm` は macOS 標準ではない。通常は Poppler 由来なので、未導入なら `brew install poppler` を使う
- 一部の実行環境では Poppler が同梱されていて追加 install なしで動くことがある

## 事前準備

- `extract` は hybrid backend が必要。`inspect` と `render` だけなら backend は不要
- `inspect` と `render` には Poppler の `pdfinfo` / `pdftoppm` が必要
- `extract` の前に、別ターミナルで毎回明示的に `opendataloader-pdf-hybrid` を起動する
- port は既定の `5002` を使えばよいので、通常は `--hybrid-url` を付けなくてよい
- 初回起動や初回変換では docling 系モデルのダウンロードが走ることがあり、ディスク 1-2 GB、メモリ 2-4 GB 程度を見込む

```bash
# macOS で Poppler が未導入なら先に入れる
brew install poppler

# 初回または更新時だけ
pip install -U "opendataloader-pdf[hybrid]"

# extract 前に起動し、"Application startup complete" まで待つ
opendataloader-pdf-hybrid --port 5002
```

- `inspect` で `pdfinfo: command not found`、`render` で `pdftoppm: command not found` が出たら Poppler 未導入を疑う
- 接続エラー時は backend 未起動をまず疑う
- 非既定の host / port で起動した場合だけ `extract --hybrid-url http://host:port` を使う
- Codex のような sandbox 環境で `Operation not permitted` が出た場合は、server の port bind と client の localhost 接続を権限付きで再実行する

## 典型手順

1. ページ範囲が不明なら `inspect`
2. 図として見たいなら `render --pages "..."` で PNG 化
3. 文字を拾いたいなら backend を起動してから `extract --pages "..."` で抽出
4. `extract` が失敗したら backend 起動ログと接続エラーを確認する
5. 必要なら `--query "..."` でヒット要素だけに絞る
6. 出力 JSON や PNG から必要部分だけを参照して回答する

## コマンド例

```bash
# Terminal 1: extract の前に起動しておく
opendataloader-pdf-hybrid --port 5002
```

```bash
# Terminal 2: 必要な操作を実行する
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py inspect docs/manual.pdf
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract docs/manual.pdf --pages "34-41" --query "PLL"
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py render docs/schematic.pdf --pages "2-3" --dpi 300
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract https://example.com/manual.pdf --pages "12-18" --table-method cluster
```

`--full-backend` は図や画像の説明も必要な場合だけ使う。

## OCR / backend オプション

- 通常のデジタル PDF はまず `opendataloader-pdf-hybrid --port 5002` で起動する
- 選択可能テキストがないスキャン PDF では `opendataloader-pdf-hybrid --port 5002 --force-ocr --ocr-lang "ja,en"` を検討する
- 既に埋め込みテキストが十分で OCR 由来の重複やノイズが出る場合は `opendataloader-pdf-hybrid --port 5002 --no-ocr` を検討する
- 図やチャートの説明を JSON / Markdown に入れたい場合は、server 側で `--enrich-picture-description`、client 側で `extract --full-backend` を併用する

## 出力運用

- 既定出力は `tmp/pdfs/`
- 文字抽出では `json` を基準にし、必要なら `markdown` も併用する
- クエリ抽出を使った場合は `<stem>.filtered.json` を優先して読む
- 画像化では `rendered/` 配下の PNG を参照する
- JSON は top-level の `pages` ではなく `kids` 配下に本文や構造が入る場合がある
- 全変換結果をそのまま会話に貼らない

## 注意

- `opendataloader-pdf` は JVM 起動コストがあるので、小分け連打よりページをまとめた 1 回の実行を優先する
- hybrid は triage で単純ページを Java、複雑な表や OCR 対象ページを backend に振り分ける。ログの `Triage summary: JAVA=..., BACKEND=...` は処理経路の確認に使える
- backend は毎回明示的に起動する方が状態が分かりやすく、接続先の取り違えも起きにくい
- ただし PDF 1 本ごとに backend を起動し直すのは UX が悪い。1 回の調査や会話ターンの間は同じ backend プロセスを使い回す
- backend 未起動時は `Could not connect to hybrid backend at http://localhost:5002` や `Hybrid server is not available at http://localhost:5002` のような接続エラーになり得る
- sandbox 環境で server 起動に失敗すると `error while attempting to bind on address ('0.0.0.0', 5002): [errno 1] operation not permitted` が出ることがある
- `--hybrid-fallback` を付けると backend 障害時も Java-only で続行できるが、精度前提が変わるので必要時だけ使う
- 回路図や図面は無理にテキスト抽出せず、先に画像化して読む
- `extract` は常に hybrid なので、通常は抽出方式の分岐判断を増やさない
