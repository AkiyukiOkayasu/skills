---
name: gndless-rust
description: Use when editing Rust code in hardware or embedded repositories, including firmware crates, shared crates, direct cargo workflows, artifact generation boundaries, and deciding when a project task runner remains appropriate.
---

# Gndless Rust

このスキルは、Rust firmware や関連 crate の作業を扱う。

## 使う場面

- `cargo` を直接使う日常作業
- firmware / updater / shared crate の作業
- バイナリ生成と静的検証の境界整理

## 基本方針

- 日常作業は `cargo` を直接使う
- task runner は、生成物配置や他ツール連携のような複合作業に残す
- 単独の `cargo fmt` / `cargo check` / `cargo test` はラッパーに閉じ込めすぎない
- 組み込み firmware では、静的検証と最終バイナリ検証を分けて考える

## 日常コマンド

- `cargo fmt`
- `cargo fmt --check`
- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo test`

組み込み target を使う場合は、プロジェクト側 target triple を付ける。  
host 実行テストが必要なら、host target を明示して `cargo test --target <host-target>` を使う。

## task runner を使う場面

- `firmware.bin` / `firmware.hex` の生成と配置
- FPGA RTL 側へ成果物を渡す
- サイズ制約を実バイナリで確認したい
- 他ツールや合成フローも含めて一気に確認したい

## 検証の基準

- `.rs` を触ったら、まず対象 crate に対して `cargo` ベースの確認を行う
- MMIO や生成物契約を変えたら、相手側も必ず更新する
- task runner があるプロジェクトでは、最後に project 標準の統合確認も行う

## アンチパターン

- `cargo check` で十分な段階なのに、毎回合成や重い統合ビルドまで回す
- hex 配置が要る処理と、純粋な Rust 静的検証を区別しない
- サイズ制約があるのに、実バイナリサイズを確認せず進める
- shared crate の変更で依存先側確認を省く

## プロジェクト固有事項

- target triple、禁止機能、サイズ制約、統合検証コマンドはプロジェクト側の skill に置く
