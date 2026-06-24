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
- 画像化は `pdftoppm` を使って PNG を出力する

## 典型手順

1. ページ範囲が不明なら `inspect`
2. 文字を拾いたいなら `extract --pages "..."` で抽出
3. 図として見たいなら `render --pages "..."` で PNG 化
4. 必要なら `--query "..."` でヒット要素だけに絞る
5. 出力 JSON や PNG から必要部分だけを参照して回答する

## コマンド例

```bash
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py inspect docs/manual.pdf
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract docs/manual.pdf --pages "34-41" --query "PLL"
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py render docs/schematic.pdf --pages "2-3" --dpi 300
python3 ~/.agents/skills/gndless-pdf/scripts/pdf_selective_ingest.py extract https://example.com/manual.pdf --pages "12-18" --table-method cluster
```

`--full-backend` は図や画像の説明も必要な場合だけ使う。

## 出力運用

- 既定出力は `tmp/pdfs/`
- 文字抽出では `json` を基準にし、必要なら `markdown` も併用する
- クエリ抽出を使った場合は `<stem>.filtered.json` を優先して読む
- 画像化では `rendered/` 配下の PNG を参照する
- 全変換結果をそのまま会話に貼らない

## 注意

- `opendataloader-pdf` は JVM 起動コストがあるので、小分け連打よりページをまとめた 1 回の実行を優先する
- 回路図や図面は無理にテキスト抽出せず、先に画像化して読む
- 常に hybrid なので、通常は抽出方式の分岐判断を増やさない
