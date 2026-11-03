---
name: gndless-pdf
description: Use when reading a PDF; extract only relevant pages/elements, or render schematics and scans as images to keep context small.
---

# Gndless PDF

`scripts/pdf_selective_ingest.py` で必要なページ・要素だけを取り出す。文字主体は抽出、回路図や図面は画像化を優先する。

## ツール

- ローカル PDF と HTTP/HTTPS の URL を受け付ける
- `inspect` は `pdfinfo`、`render` は `pdftoppm` を使う (未導入なら `brew install poppler`)
- `extract` は hybrid backend が必要。`inspect` と `render` だけなら不要

## extract の準備

```bash
pip install -U "opendataloader-pdf[hybrid]"   # 初回・更新時だけ
opendataloader-pdf-hybrid --port 5002          # "Application startup complete" まで待つ
```

- 通常は既定 port `5002`。非既定の host / port のときだけ `extract --hybrid-url http://host:port`
- 初回起動・初回変換は docling 系モデルのダウンロードでディスク 1-2 GB、メモリ 2-4 GB 程度
- 図の説明も要る場合だけ server の `--enrich-picture-description` と `extract --full-backend` を併用する
- `Could not connect to hybrid backend` は backend 未起動を疑う。sandbox の `Operation not permitted` は port bind と localhost 接続を権限付きで再実行する
- 1回の調査では同じ backend プロセスを使い回す

## OCR

`--force-ocr` / `--no-ocr` / `--ocr-*` は `extract` ではなく backend 起動側のオプション。`--force-ocr` と `--no-ocr` は排他。

- 選択可能テキストが無いスキャン PDF: `--force-ocr --ocr-lang "ja,en"`
- 埋め込みテキストが十分で OCR が重複する場合: `--no-ocr`
- OCR 品質が悪い PDF は無理に `extract` せず `render` を優先する
- `--ocr-lang` のコード体系は `--ocr-engine` に依存する。EasyOCR (既定) は ISO 639-1 (`ja,en`)、Tesseract は ISO 639-2 (`jpn,eng`)、RapidOCR は `english,chinese`、ocrmac は BCP-47 (`ja-JP`)
- `--ocr-engine` は `auto` / `easyocr` / `nemotron-ocr` / `ocrmac` / `rapidocr` / `tesseract` / `tesserocr`。`auto` はページごとに docling が選ぶ。`--psm` は tesseract / tesserocr のときだけ有効
- hybrid は triage で単純ページを Java、複雑な表や OCR 対象を backend に振り分ける。ログの `Triage summary: JAVA=..., BACKEND=...` で経路を確認できる

## 手順

1. ページ範囲が不明なら `inspect`
2. 図として見たいなら `render --pages "..."` で PNG 化する (回路図・図面を無理にテキスト抽出しない)
3. 文字を拾うなら backend を起動して `extract --pages "..."`、必要なら `--query "..."` でヒット要素に絞る
4. 出力 JSON / PNG の必要部分だけを参照する

```bash
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py inspect docs/manual.pdf
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract docs/manual.pdf --pages "34-41" --query "PLL"
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py render docs/schematic.pdf --pages "2-3" --dpi 300
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract https://example.com/manual.pdf --pages "12-18" --table-method cluster
```

## 出力

- 既定出力は `tmp/pdfs/`。文字抽出は JSON を基準にし、必要なら Markdown も併用する
- query 抽出では `<stem>.filtered.json` を優先して読む
- 画像化では `rendered/` 配下の PNG を参照する
- JSON の本文や構造は top-level の `pages` ではなく `kids` 配下にある場合がある
- 根拠が必要なときは page number と bounding box を維持する
- 全変換結果をそのまま会話に貼らない

`opendataloader-pdf` は JVM 起動コストがあるため、小分け連打よりページをまとめた1回の実行を優先する。`--hybrid-fallback` は backend 障害時も Java-only で続行できるが、精度前提が変わるので必要時だけ使う。
