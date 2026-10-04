---
name: gndless-release
description: Use when preparing a repository release, including version bump verification, release notes, tagging, and pre-release validation.
---

# Gndless Release

リポジトリのリリース手順。タグはセマンティックバージョニングの `vX.Y.Z` (例: `v0.5.2`, `v0.6.0`) を使う。

## 手順

1. バージョン文字列や公開 artifact に影響する箇所、トップレベルの仕様変更点を確認
2. `git log --oneline 前回タグ..HEAD` でリリースログの元になる変更履歴を取得
3. リリースノートの Unreleased セクションを日付とバージョンタグへ確定し、コミット
4. プロジェクト標準の検証を完了する (言語ごとの静的検証、生成物を含む統合ビルド、サイズ・タイミング制約、release artifact の生成確認)
5. `git tag -a vX.Y.Z -m "vX.Y.Z"` して `git push origin <default-branch> --tags`

## リリースノート

Unreleased セクションでは少なくとも次を整理する。

- 追加機能 / 変更点
- 破壊的変更の有無
- 既知の制約や移行上の注意
- ハードウェア割り当てや UI アサインなど、利用者が確認すべき差分

## アンチパターン

- リリースノートを更新せずにタグを打つ
- タグ後に検証して制約違反が発覚する
- 前回タグからの変更を `git log` で確認せず、記憶だけでリリースノートを書く
- タグをプッシュしてからコミット漏れに気づく
