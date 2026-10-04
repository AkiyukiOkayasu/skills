---
name: gndless-pdf
description: Use when inspecting a local or web PDF, extracting only relevant pages or elements, or rendering visually dense pages such as schematics and scanned drawings while keeping context usage low.
---

# Gndless PDF

`opendataloader-pdf` を前処理に使い、必要なページや要素だけを reasoning に渡す。文字主体の PDF は抽出、回路図や図面のような視覚主体の PDF は画像化を優先する。

## ツール

- 実体は `scripts/pdf_selective_ingest.py`
- ローカル PDF と HTTP/HTTPS の PDF URL を両方受けられる
- `inspect` は `pdfinfo`、`render` は `pdftoppm` を使う (macOS 標準ではない。未導入なら `brew install poppler`)
- `extract` は hybrid backend が必要。`inspect` と `render` だけなら backend は不要

## extract の準備

```bash
pip install -U "opendataloader-pdf[hybrid]"   # 初回または更新時だけ
opendataloader-pdf-hybrid --port 5002          # extract 前に起動し、"Application startup complete" まで待つ
```

- 通常は既定 port `5002` を使う。非既定の host / port で起動した場合だけ `extract --hybrid-url http://host:port` を付ける
- 初回起動や初回変換では docling 系モデルのダウンロードが走り、ディスク 1-2 GB、メモリ 2-4 GB 程度を見込む
- 図やチャートの説明も要る場合だけ、server の `--enrich-picture-description` と client の `extract --full-backend` を併用する
- `Could not connect to hybrid backend` などの接続エラーは backend 未起動をまず疑う。sandbox の `Operation not permitted` は port bind と localhost 接続を権限付きで再実行する
- 1 回の調査や会話ターンの間は同じ backend プロセスを使い回す

## OCR / backend オプション

`--force-ocr` / `--no-ocr` / `--ocr-*` は `extract` ではなく backend 起動側のオプション。`--force-ocr` と `--no-ocr` は排他。

- 選択可能テキストがないスキャン PDF: `opendataloader-pdf-hybrid --port 5002 --force-ocr --ocr-lang "ja,en"`
- 埋め込みテキストが十分で OCR による重複テキストが出る場合: `--no-ocr`
- OCR 品質が悪くテキスト抽出が崩れる PDF は、無理に `extract` せず `render` を優先する
- `--ocr-lang` のコード体系は `--ocr-engine` に依存する。EasyOCR (既定) は ISO 639-1 (`ja,en`)、Tesseract は ISO 639-2 (`jpn,eng`)、RapidOCR は `english,chinese`、ocrmac は BCP-47 (`ja-JP`)
- `--ocr-engine` (`auto` / `easyocr` / `nemotron-ocr` / `ocrmac` / `rapidocr` / `tesseract` / `tesserocr`、既定は easyocr) はエンジンごとに言語対応・精度・ライセンスが異なる。`auto` はページごとに docling に選択を委ねる。`--psm` は tesseract / tesserocr のときだけ有効
- hybrid は triage で単純ページを Java、複雑な表や OCR 対象ページを backend に振り分ける。ログの `Triage summary: JAVA=..., BACKEND=...` で処理経路を確認できる

## 典型手順

1. ページ範囲が不明なら `inspect`
2. 図として見たいなら `render --pages "..."` で PNG 化 (回路図・図面は無理にテキスト抽出しない)
3. 文字を拾いたいなら backend を起動して `extract --pages "..."`、必要なら `--query "..."` でヒット要素だけに絞る
4. 出力 JSON / PNG の必要部分だけを参照して回答する

```bash
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py inspect docs/manual.pdf
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract docs/manual.pdf --pages "34-41" --query "PLL"
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py render docs/schematic.pdf --pages "2-3" --dpi 300
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract https://example.com/manual.pdf --pages "12-18" --table-method cluster
```

## 出力

- 既定出力は `tmp/pdfs/`。文字抽出は `json` を基準にし、必要なら `markdown` も併用する
- query 抽出では `<stem>.filtered.json` を優先して読む
- 画像化では `rendered/` 配下の PNG を参照する
- JSON の本文や構造は top-level の `pages` ではなく `kids` 配下にある場合がある
- 根拠が必要なときは page number と bounding box を維持する
- 全変換結果をそのまま会話に貼らない

## 注意

- `opendataloader-pdf` は JVM 起動コストがあるため、小分け連打よりページをまとめた 1 回の実行を優先する
- `--hybrid-fallback` は backend 障害時も Java-only で続行できるが、精度前提が変わるので必要時だけ使う
