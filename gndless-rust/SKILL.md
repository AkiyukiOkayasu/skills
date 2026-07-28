---
name: gndless-rust
description: Use when editing Rust code in hardware or embedded repositories, including firmware crates, shared crates, cargo-based verification, and integration points with generated artifacts.
---

# Gndless Rust

このスキルは、Rust firmware や関連 crate の作業を扱う。

## 使う場面

- `cargo` を直接使う日常作業
- firmware / updater / shared crate の作業
- バイナリ生成と静的検証の境界整理

## 基本方針

- まず対象 crate 単位で `cargo` による確認を行う
- 組み込み firmware では、静的検証と最終バイナリ検証を分けて考える
- 生成物や他言語との境界がある変更は、契約先もセットで確認する

## Documentation comments

- Rust の doc comment の慣習に従い、公開 API、module、型、field、function、定数など利用者が契約を理解する必要がある対象には `///` を使い、crate-level documentation には `//!` を使う。

### 日本語

- 主に自分が使うプロジェクトでは本文を日本語で記載する。既存のプロジェクト方針、公開 API の言語、周辺の doc comment が別の規約を定めている場合は、その方針を優先する。
- 簡単な英語の専門用語や短い複合語は英語のまま記載し、`AES3 professional transmitter` を `AES3 professional送信機` のような不自然な和英混在へ変換しない
- 見出しや箇条書きなど1行で完結する記述は末尾に句点を付けず、日本語の文末は「〜する」より「〜を確認」「〜を記載」のような体言止めを優先
- 見出しや箇条書き以外の複数行にわたる詳細説明は、各文の末尾に句点を付加

### 構成

- 説明の先頭に対象の役割や基本動作を短くまとめ、その後に必要な詳細を書く。実装を言い換えるだけでなく、利用条件、保証、状態変化、副作用、エラー、panic、安全性など利用者が判断に必要とする情報を記載する。
- `Arguments`、`Returns`、`Errors`、`Panics`、`Safety`、`Examples` など、簡単な英語の方が分かりやすい定型見出しは英語で記載する。見出しの下の説明は原則日本語で記載する。
- 文の途中では改行しない。1行あたりの文字数制限は設けず、段落、箇条書き、コードブロックなどMarkdown上の意味の区切りで改行する。
- doc comment の例は可能な限り `rustdoc` で実行可能な形にし、APIの使い方と期待される結果が分かる最小限の例にする。

## 日常コマンド

- `cargo fmt`
- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`

mixed host / embedded 構成では、対象 crate のディレクトリへ移動してから `cargo` を実行する。  
`--manifest-path` だけで repo ルートから実行すると、その crate 配下の `.cargo/config.toml` にある
`build.target` などを期待どおり拾えないことがある。

組み込み target を使う場合は、まず対象 crate ディレクトリでプロジェクト側 `.cargo/config.toml` を使う。  
crate ディレクトリ外から実行する必要がある場合だけ、target triple を明示的に付ける。  
host 実行テストが必要なら、host target を明示して `cargo test --target <host-target>` を使う。

## 検証の基準

- `.rs` を触ったら、まず対象 crate に対して `cargo` ベースの確認を行う
- MMIO や生成物契約を変えたら、相手側も必ず更新する
- サイズ制約があるなら、最終バイナリでも確認する
- 生成物を他ツールへ渡す構成なら、反映先との整合も確認する

## 組み込みRustの注意点

- target環境に依存しないロジックは、独立したno_std crateとして切り出し、host環境でtestする
- 常にreleaseビルドを使用する。組み込みではdebugビルドは最終生成物のサイズや性能の問題から使わない
- cargo-binutilsでバイナリサイズやセクション情報を確認することができる
- Cargo.tomlのprofile設定で、以下のものから始める。ROMサイズの制限が厳しい場合は、debug = falseにしてもよい。

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
- 静的検証と最終生成物確認を区別しない
- サイズ制約があるのに、実バイナリサイズを確認せず進める
- shared crate の変更で依存先側確認を省く

## プロジェクト固有事項

- target triple、禁止機能、サイズ制約、生成物配置先、統合検証コマンドはプロジェクト側の skill に置く
