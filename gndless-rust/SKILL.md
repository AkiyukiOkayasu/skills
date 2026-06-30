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

## 日常コマンド

- `cargo fmt`
- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`

組み込み target を使う場合は、プロジェクト側 target triple を付ける。  
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
