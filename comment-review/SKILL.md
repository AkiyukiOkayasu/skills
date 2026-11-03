---
name: comment-review
description: Use when writing or reviewing code comments; keep why, external constraints, and non-obvious contracts, and drop history and restatement.
---

# Comment Review

コメントには、コードを読むだけでは分からないことだけを書く。

## 書く

- なぜそうしているか (一見奇妙な実装の理由)
- 外部制約 (実機事情、仕様、依存先の制約)
- 呼び出し側が知るべき非自明な契約・前提

## 書かない

- 試行錯誤や経緯 (当初は〜、いろいろ試した結果〜)
- 修正履歴 (バグを直した、追加した)
- コードの言い換え
- 1文で言い切れない背景説明 (設計文書やコミットメッセージへ)
- 文の途中での改行。1文は1行で書く。行末が `、` や助詞 (の/で/し/が/を/に/は/と/も/ため/ので/から/まで/より) なら文が途中。コメントに行長制限は適用しない

## レビュー

1. 対象をコメント行に絞る (コードロジックは対象外)
2. 各コメントを OK / 修正 / 削除 で判定し、修正案を1行で添える
3. 非自明な why が抜けている箇所は追加を提案する

```rust
// NG: 当初は SPI で読んでいたがノイズで不安定だったため、I2C に切り替えた
let data = read_i2c();

// OK: 読み取りは I2C に限定 (SPI はノイズで不安定なため)
let data = read_i2c();

// NG: データの長さを2バイトで表す
let len = (data.len() as u16) << 8;

// OK: length は big-endian で格納される
let len = (data.len() as u16) << 8;
```
