---
name: gndless-git
description: Use when creating branches, staging changes, writing commits, or preparing history in hardware and firmware projects, with lightweight branch naming and Japanese commit subjects with structured bodies.
---

# Gndless Git

ハードウェア / ファームウェア系プロジェクトで使い回す git 運用規約。

## ブランチ名

- 英語の短いケバブケースか単語列で、1 ブランチ 1 テーマ
- 問題領域を先頭に置く。迷ったら `area-action` か `area-topic`

例: `updater-sd-timing`, `picorv-mmio-cleanup`, `gowin-project-init`, `veryl-register-sync`

## コミットメッセージ

1 行目は次のいずれかの prefix で始め、本文は日本語で書く。

- `add:`
- `fix:`
- `BREAKING CHANGE:`
- `ci:`
- `update:`
- `remove:`

例:

- `fix: updater のSD起動待ち時間を100msに延ばす`
- `add: Gowin project 生成用のTcl手順をSKILL化する`
- `update: just依存を整理してVerylとRustのSKILLを分離する`

コード差分だけでは読み取れない補足は、3 行目以降に書く。

```text
fix: updater のSD起動待ち時間を100msに延ばす

一部のカードで電源投入直後の初回コマンド失敗が残っていたため。
100ms は実機観測で安定した最小寄りの値。
```

書くべき情報: なぜ必要だったか、実機事情や制約、代替案を採らなかった理由、互換性影響や運用注意。

## コミット単位

- リファクタと挙動変更は原則分ける
- generated file を含むなら、元ソース変更と因果が追える単位にする
- unrelated change を混ぜない

## アンチパターン

- 英語 prefix のあとを英語本文にする
- 1 行目だけで背景が足りないのに本文を空にする
- 無関係な変更をひとつのコミットに詰める
- ブランチ名に日付や雑多な接頭辞を無秩序に入れる
