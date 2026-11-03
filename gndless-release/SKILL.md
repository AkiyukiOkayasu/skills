---
name: gndless-release
description: Use when releasing a repo; confirm version and changes, write release notes, run pre-release checks, and tag vX.Y.Z.
---

# Gndless Release

タグはセマンティックバージョニングの `vX.Y.Z` (例: `v0.5.2`, `v0.6.0`)。

## 手順

1. バージョン文字列、公開 artifact、トップレベルの仕様変更点を確認する
2. `git log --oneline 前回タグ..HEAD` でリリースノートの元になる変更履歴を取得する
3. Release notes の Unreleased を日付とバージョンタグへ確定し、コミットする
4. プロジェクト標準の検証を完了する (静的検証、生成物を含む統合ビルド、サイズ・タイミング制約、release artifact の生成確認)
5. `git tag -a vX.Y.Z -m "vX.Y.Z"` して `git push origin <default-branch> --tags`

## リリースノート

- 追加機能 / 変更点
- 破壊的変更の有無
- 既知の制約や移行上の注意
- ハードウェア割り当てや UI アサインなど、利用者が確認すべき差分

## 注意

- リリースノートを更新せずにタグを打たない
- タグを push する前に、検証とコミット漏れを確認する
- 前回タグからの変更を `git log` で確認せず、記憶だけで書かない
