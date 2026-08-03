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

## コード委譲

- 広い差分の分類、変更履歴の索引、commit対象候補・メッセージ案の整理、関連文書の下書き、巨視的な独立レビューが必要な場合は `$delegate-agent` を使う。
- `$delegate-agent` では `explore` を差分や履歴の把握、`review` を巨視的レビュー、`commit-prep` をコミット候補整理に使う。`work` は通常不要で、必要でも判断余地の少ない文書修正などに限る。
- `$delegate-agent` の既定委譲モデルは高速・低コストな広域探索向けのものを想定する。staging範囲、既存変更との境界、履歴の意味、commit単位、prefix、最終diffとcommit内容の細かな確認はGPT/Codexが担当する。
- `review` は外部レビュー全般を意味せず、ここでは `$delegate-agent` による独立した巨視的レビューを指す。staging境界や個別diffの確認はGPT/Codexで行う。
- `explore` や `commit-prep` の結果は候補・索引として扱い、対象path、差分、テスト、コミット操作の最終判断はCodexが行う。
- 大きな差分の整理、コミット対象の洗い出し、独立レビューが必要な場合だけ `$delegate-agent` を使う。小さい変更や単一ファイルの既知の変更では委譲しない。
- コミット前の候補整理は `commit-prep`、広い差分の欠陥確認は `review`、対象範囲が不明な場合の把握は `explore` を使う。
- `commit`は実装・Codex確認後の別工程として扱い、対象pathの明示、限定stage、push禁止を必須にする。現行runnerでは直接commitを有効化していないため、当面は`commit-prep`後にCodexがcommitする。
- 小さい変更や単一ファイルの既知の変更では委譲しない。委譲先に既存変更の破棄、reset、rebase、amend、pushをさせない。

例:

```bash
delegate-agent/scripts/delegate-agent \
  --mode commit-prep \
  --goal "現在の差分からコミット対象とメッセージ案を整理する" \
  --acceptance "対象ファイル、テスト状況、コミットメッセージ案を根拠付きで報告する" \
  --scope src
```

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
