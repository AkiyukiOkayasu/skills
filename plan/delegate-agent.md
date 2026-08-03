# OpenCode Go / DeepSeek委譲方針

## 現在の状態

- `delegate-agent` を共通入口として追加済み
- `explore` / `review` / `work` / `commit-prep` の契約を文書化済み
- domain Skill からは `$delegate-agent` を呼ぶ構成へ整理済み
- 現在の runner は `commit-prep` までを公開し、直接 `commit` は未公開

## 残作業

- [ ] 明示許可付きのcommitモードをrunnerへ実装するか、安全なcommit-prep運用で確定する
- [ ] 実リポジトリで各用途の速度・品質・検証コストを確認

## 明示許可付きのcommitモードをrunnerへ実装するか、安全なcommit-prep運用で確定する

直接 `commit` を公開するなら、少なくとも次を満たす。

- 対象 path の明示
- 対象外変更の混入検知
- broad stage の禁止
- push 禁止
- parent 側での差分・テスト確認後だけ実行

これを満たすまで、既定運用は `commit-prep` と Codex 側の手動 commit の組み合わせとする。

## 実リポジトリで各用途の速度・品質・検証コストを確認

少なくとも次の用途で、delegate の往復時間だけでなく Codex 側の再確認コストも含めて評価する。

- 広域 `explore`
- 巨視的 `review`
- 明確な Plan に沿う小規模 `work`
- `commit-prep`

評価時は、速度だけでなく次も確認する。

- 重要な構造把握の取りこぼし
- 巨視的レビューの有効性と誤検出
- `work` の対象外変更の有無
- Codex 側での検証負荷
