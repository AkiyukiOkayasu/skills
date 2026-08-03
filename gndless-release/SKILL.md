---
name: gndless-release
description: Use when preparing a repository release, including version bump verification, release notes updates, tagging, and pre-release validation.
---

# Gndless Release

このスキルは、リポジトリのリリース手順を扱う。

## 使う場面

- リリース作業に入る前
- リリースノートを更新する
- タグを打つ
- 前回リリースからの変更を確認する

## リリース前確認リスト

以下を確認してからタグ付けする。

1. バージョン文字列や公開 artifact に影響する箇所を確認
2. トップレベルの仕様変更点を確認
3. `git log --oneline 前回タグ..HEAD` でリリースログの元になる変更履歴を取得
4. リリースノートの Unreleased セクションを更新し、日付とバージョンタグへ確定する

## コード委譲

- 前回タグからの広い変更の索引、release noteやdocumentの整理、リリース対象・コミット候補整理、巨視的な変更レビューでは、必要に応じて `$delegate-agent` を利用する。
- モード説明、共通安全規則、出力の扱いは `$delegate-agent` に従う。
- version、artifact、互換性、build・test・size・timingなどのrelease gate、個別差分の細かなレビュー、最終的なリリース可否、タグ付け、コミット、pushはCodexが検証後に判断・実行する。
- 委譲結果だけでリリース可否を決めず、必須のbuild、test、artifact検証を省略しない。

## タグ命名規則

- 形式: `vX.Y.Z` （セマンティックバージョニング）
- 例: `v0.5.2`, `v0.6.0`

## タグ付け手順

```bash
# リリースノートを更新したらコミット
git add <release-notes-file>
git commit -m "update: vX.Y.Z リリースノートを追記"

# タグを打つ
git tag -a vX.Y.Z -m "vX.Y.Z"

# プッシュ
git push origin <default-branch> --tags
```

## 最終確認

タグを打つ前に、**必ず** プロジェクト標準の検証を完了する。

- 言語ごとの静的検証
- 生成物を含む統合ビルド
- サイズ制約やタイミング制約の確認
- リリース artifact が期待どおり生成されることの確認

## リリースノートの書き方

Unreleased セクションでは、少なくとも以下を整理する。

- 追加機能 / 変更点
- 破壊的変更の有無
- 既知の制約や移行上の注意
- ハードウェア割り当てや UI アサインなど、利用者が確認すべき差分

## 参照

- リリースノート本体
- リポジトリの workflow / release 手順
- タグ前に必要な build / test 手順

## アンチパターン

- リリースノートを更新せずにタグを打つ
- タグ後に検証して制約違反が発覚する
- 前回タグからの変更を `git log` で確認せず、記憶だけでリリースノートを書く
- タグをプッシュしてからコミット漏れに気づく
