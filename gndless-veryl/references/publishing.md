# Dependency updates and publishing

Veryl dependency、toolchain、公開 API の更新や publish を行う場合に参照する。

## Dependency / toolchain update

- Veryl は1.0未満で spec・standard library API が変わり得るため、release note と migration 結果を確認
- `veryl migrate --check` を先に実行
- migration 後は `veryl fmt`、`veryl check`、`veryl test`、`veryl build` を実行
- Veryl source、生成 RTL、filelist、module hierarchy の diff を確認
- 旧 version との compatibility を過度に維持しない

## Publish

1. `Veryl.toml` の version を更新し、その変更だけを commit
2. `veryl publish` を実行
3. `Veryl.pub` の version と commit の対応を確認し、`Veryl.pub` だけを別 commit

`Veryl.toml` と `Veryl.pub` を同じ commit にまとめない。
