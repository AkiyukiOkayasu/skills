---
name: gndless-git
description: Use when branching or committing in this user's hardware/firmware repos; use kebab-case branch names and Japanese commit subjects with fixed prefixes.
---

# Gndless Git

## ブランチ

- 英語の短いケバブケースで1ブランチ1テーマ
- 問題領域を先頭に置く (`updater-sd-timing`, `gowin-project-init`)

## コミットメッセージ

1行目は次の prefix で始め、本文は日本語で書く。

- `add:`
- `fix:`
- `update:`
- `remove:`
- `ci:`
- `BREAKING CHANGE:`

本文には、コード差分から読み取れない理由、実機事情や制約、代替案を採らなかった理由、互換性影響を書く。

```text
fix: updater のSD起動待ち時間を100msに延ばす

一部のカードで電源投入直後の初回コマンド失敗が残っていたため。
100ms は実機観測で安定した最小寄りの値。
```

## コミット単位

- リファクタと挙動変更は分ける
- generated file を含む場合は元ソース変更と因果が追える単位にする
- 無関係な変更を混ぜない
