---
name: gndless-rust
description: Use when editing Rust in hardware or embedded repositories, including firmware crates, shared crates, cargo-based verification, and generated-artifact boundaries.
---

# Gndless Rust

Rust firmware / crate 作業の規約と注意点。

## Documentation comments

- 公開 API、module、型、field、function、定数など契約を示す対象には `///`、crate-level documentation には `//!` を使う
- 簡単な英語の専門用語や短い複合語（`AES3 professional transmitter` など）は英語のまま書く
- `Arguments`、`Returns`、`Errors`、`Panics`、`Safety`、`Examples` など定型見出しは英語、本文は原則日本語（project の既存方針を優先）
- 説明の先頭に役割や基本動作を短くまとめ、後に利用条件、保証、状態変化、副作用、エラー、panic、安全性などの契約を書く
- 見出し・箇条書きは体言止め・句点なし、複数行の詳細説明は各文の末尾に句点
- 文の途中では改行しない。段落・箇条書き・code block など Markdown 上の意味の区切りだけで改行する
- 例は可能な限り `rustdoc` で実行可能にし、使い方と期待結果が分かる最小限にする

## 日常コマンド

- `cargo fmt`
- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`

mixed host / embedded 構成では、対象 crate のディレクトリへ移動してから `cargo` を実行する。`--manifest-path` だけで repo ルートから実行すると、その crate 配下の `.cargo/config.toml` にある `build.target` などを期待どおり拾えないことがある。

組み込み target を使う場合は、まず対象 crate ディレクトリでプロジェクト側 `.cargo/config.toml` を使う。crate ディレクトリ外から実行する必要がある場合だけ target triple を明示的に付ける。host 実行テストが必要なら `cargo test --target <host-target>` を使う。

## 検証の基準

- `.rs` を触ったら、まず対象 crate に対して `cargo` ベースの確認を行う
- 組み込みでは静的検証と最終バイナリ検証を分けて考える
- MMIO や生成物契約を変えたら、相手側も必ず更新する
- 生成物を他ツールへ渡す構成なら、反映先との整合も確認する
- サイズ制約があるなら、最終バイナリでも確認する

## 組み込みRustの注意点

- target環境に依存しないロジックは、独立したno_std crateとして切り出し、host環境でtestする
- 常にreleaseビルドを使用する。組み込みではdebugビルドは最終生成物のサイズや性能の問題から使わない
- cargo-binutilsでバイナリサイズやセクション情報を確認することができる
- Cargo.tomlのprofile設定で、以下のものから始める。ROMサイズの制限が厳しい場合は、debug = falseにしてもよい

```Cargo.toml
[profile.release]
debug = 2
lto = true
opt-level = 'z'

[profile.dev]
debug = 2
lto = true
opt-level = "z"
```

## アンチパターン

- `cargo check` で十分な段階なのに、毎回重い統合ビルドやclippyまで回す
- サイズ制約があるのに、実バイナリサイズを確認せず進める
- shared crate の変更で依存先側確認を省く
