---
name: gndless-rust
description: Use when editing Rust firmware or crates, including Rust doc comment conventions, crate-local cargo invocation, and embedded release profiles.
---

# Gndless Rust

## Documentation comments

- 公開 API、module、型、field、function、定数など契約を示す対象には `///`、crate-level documentation には `//!` を使う
- `Arguments`、`Returns`、`Errors`、`Panics`、`Safety`、`Examples` など定型見出しは英語、本文は日本語 (project の既存方針を優先)
- 英語の専門用語や短い複合語 (`AES3 professional transmitter` など) は英語のまま書く
- 説明の先頭に役割や基本動作を短くまとめ、後に利用条件、保証、状態変化、副作用、エラー、panic、安全性などの契約を書く
- 見出し・箇条書きは体言止め・句点なし、複数行の詳細は各文末に句点
- 1文は1行。段落・箇条書き・code block など Markdown 上の区切りだけで改行する
- 例は可能な限り rustdoc で実行可能にし、使い方と期待結果が分かる最小限にする

## 検証

- `.rs` を触ったら対象 crate で `cargo fmt`、`cargo check` を実行する。必要に応じて `cargo clippy -- -D warnings`、`cargo test`
- mixed host / embedded 構成では crate ディレクトリへ移動してから `cargo` を実行する。`--manifest-path` だけだと crate 配下の `.cargo/config.toml` (`build.target` など) を拾えないことがある
- 組み込み target ではプロジェクト側 `.cargo/config.toml` を優先し、crate 外から実行するときだけ target triple を明示する。host test は `cargo test --target <host-target>`
- MMIO や生成物契約を変えたら相手側も更新し、サイズ制約があれば最終バイナリで確認する

## 組み込み

- target に依存しないロジックは no_std crate として切り出し、host で test する
- 組み込みでは release build を使う
- `cargo-binutils` でバイナリサイズとセクション情報を確認できる
- プロファイルは次から始める。ROM 制限が厳しければ release の `debug = false` にする

```toml
[profile.release]
debug = 2
lto = true
opt-level = "z"

[profile.dev]
debug = 2
lto = true
opt-level = "z"
```
