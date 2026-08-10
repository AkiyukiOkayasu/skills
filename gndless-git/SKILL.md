---
name: gndless-git
description: Use when creating branches, staging changes, writing commits, or preparing history, especially when lightweight branch naming, Japanese commit subjects, and structured commit bodies need to stay consistent across hardware and firmware projects.
---

# Gndless Git

このスキルは、ハードウェア / ファームウェア系プロジェクトで使い回しやすい git 運用規約を扱う。

## 使う場面

- ブランチを切る
- コミットする
- 変更を論理単位に分ける
- コミットメッセージや履歴を整える

## 独立レビュー

- 広い差分の分類、変更履歴の索引、コミット候補整理、関連文書の下書き、巨視的な独立レビューでは、必要に応じて `codex-reviewer` subagentを利用する（読み取り専用、変更はしない）。
- staging範囲、既存変更との境界、履歴の意味、commit単位、prefix、最終diff確認、実際のstage/commitはopencodeが担当する。
- 小さい変更や単一ファイルの既知の変更ではレビューを省略できる。

## ブランチ名

新規ブランチ名の方針:

- 英語の短いケバブケースか単語列
- 1 ブランチ 1 テーマ
- 問題領域を先頭に置く
- 迷ったら `area-action` か `area-topic`

例:

- `updater-sd-timing`
- `picorv-mmio-cleanup`
- `gowin-project-init`
- `veryl-register-sync`

## コミットメッセージ規約

1 行目は必ず次のいずれかの prefix で始める。

- `add:`
- `fix:`
- `BREAKING CHANGE:`
- `ci:`
- `update:`
- `remove:`

1 行目の本文は日本語で書く。  
例:

- `fix: updater のSD起動待ち時間を100msに延ばす`
- `add: Gowin project 生成用のTcl手順をSKILL化する`
- `update: just依存を整理してVerylとRustのSKILLを分離する`

## 追加説明の書き方

コード差分だけでは読み取れない補足は、コミットメッセージを改行して 3 行目以降に書く。

形式:

```text
fix: updater のSD起動待ち時間を100msに延ばす

一部のカードで電源投入直後の初回コマンド失敗が残っていたため。
100ms は実機観測で安定した最小寄りの値。
```

書くべき情報:

- なぜ必要だったか
- 実機事情や制約
- 代替案を採らなかった理由
- 互換性影響や運用注意

## コミット単位

- リファクタと挙動変更は原則分ける
- generated file を含むなら、元ソース変更と因果が追える単位にする
- unrelated change を混ぜない

## プロジェクト固有事項

- repo 固有の workflow、タグ運用、生成物配置、検証コマンドはプロジェクト側の skill に置く
- このスキルには再利用できる git 規約だけを残す

## アンチパターン

- 英語 prefix のあとを英語本文にする
- 1 行目だけで背景が足りないのに本文を空にする
- `WIP` や曖昧な題名で履歴を残す
- 無関係な変更をひとつのコミットに詰める
- ブランチ名に日付や雑多な接頭辞を無秩序に入れる
