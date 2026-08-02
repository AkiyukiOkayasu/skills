# Dependency updates and publishing

Veryl dependency、toolchain、公開 API の更新や publish を行う場合に参照する。

## Dependency / toolchain update

- Veryl は1.0未満で spec・standard library API が変わり得るため、release note と migration 結果を確認
- `veryl migrate --check` を先に実行
- migration 後は `veryl fmt`、`veryl check`、`veryl test`、`veryl build` を実行
- Veryl source、生成 RTL、filelist、module hierarchy の diff を確認
- 旧 version との compatibility を過度に維持しない

## Publish

1. 新バージョンがmajor, minor, patchによるリリースなのかをCHANGELOG.mdやコミットログから判断し、人間に確認を取る
2. CHANGELOG.mdなどの未リリース情報を新バージョンで確定させてcommit
3. Veryl.tomlのpublish設定に下記のbump_commit = trueとpublish_commit = trueが含まれているか確認する
4. `veryl publish --bump xxx` を実行。xxxはpatch, minor, majorのいずれか。

```toml
[publish]
bump_commit = true
publish_commit = true
```
