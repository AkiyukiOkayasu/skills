---
name: gndless-veryl
description: Use when editing Veryl RTL, documentation comments, project configuration, tests, generated RTL, dependencies, or publish flows.
---

# Gndless Veryl

Veryl RTL の編集、検証、documentation、生成 RTL、dependency、publish を扱う。

## 基本方針

- project 固有の `Veryl.toml`、toolchain、下流 build script、他の skill を先に確認
- `.veryl` を正とし、`target/` などの生成 `.sv`、`.sv.map`、`.f` は直接編集しない
- 構文だけでなく、生成回路の wire/register、bit width、signedness、logic depth、RAM/FF inference、reset cost、clock domain を確認
- board、register map、Fmax、vendor flow など project 固有事項は project 側の skill を優先

## コード委譲

- RTL hierarchy、module間接続、生成物の入口、関連testの横断探索、承認済みPlanに沿う明確な修正・文書化、広い差分の巨視的レビューが必要な場合は、まず `$delegate-agent` を使う。
- `$delegate-agent` では `explore` を横断探索、`review` を巨視的レビュー、`work` を判断余地の少ない小規模修正、`commit-prep` をコミット候補整理に使う。
- `$delegate-agent` の既定委譲モデルは高速・低コストな広域探索向けのものを想定する。diagnosticからsourceへの詳細追跡、width・signedness・CDC・reset・timing・inferenceの詳細設計、generated RTLとの照合、細かな実装レビュー、最終検証はGPT/Codexが担当する。
- `review` は外部レビュー全般を意味せず、ここでは `$delegate-agent` による独立した巨視的レビューを指す。width、CDC、reset、timingなどの詳細確認はGPT/Codexで行う。
- `explore` の結果は索引・仮説として扱い、module hierarchy、port契約、信号幅、生成元との対応はCodexがsource・map・生成RTLで再確認する。
- 大きな `.veryl`／生成RTL差分の `review` 結果を採用する前に、`--scope` をsourceと必要なtestに限定し、Codexで `veryl fmt/check/test/build` を実行する。

## Documentation comments

- doc comment を追加・編集する場合は [references/documentation.md](references/documentation.md) を読む
- 公開 module、interface、function、型、port、parameter、const の契約を記載
- Mermaid と WaveDrom を積極的に使い、利用可能なら `wavedrom,test` を優先

## Workflow

`.veryl` を変更したら対象 project で原則として次を実行する。

```text
veryl fmt
veryl check
veryl test
veryl build
```

- 小さな unit test と native test を優先し、長い test は必要時だけ `veryl test --ignored`
- backend 差の確認は `veryl test --backend-validate`、`--wave` は失敗再現・波形解析時だけ使用
- system-level の性質だけ project 側の外部 simulation workflow を併用
- migration、dependency update、publish は [references/publishing.md](references/publishing.md) を読む

## Naming and types

- project の既存規約を優先し、規約がなければ file/function/local/instance/port は `snake_case`、public module/interface は `UpperCamelCase`、param/const は `UPPER_SNAKE_CASE`、package は `PascalCase`
- port は方向 prefix/suffix ではなく意味名を使い、clock は `clk`、system reset は `rst`
- public port、module 契約、register/accumulator の width、signedness が重要な境界では型を明示
- FSM は enum、関連する pipeline/bus signal は struct を検討し、public transaction と internal transaction は分離
- cast、width 変更、signed/unsigned 変換を扱う場合は [references/casting.md](references/casting.md) を読む
- generic、Boolean type、packed/unpacked、system function/task を扱う場合は [references/language-notes.md](references/language-notes.md) を読む

## RTL design

- `always_comb` は output/next-state を先頭で default assignment し、全経路で代入
- `always_ff` の `=` は nonblocking 相当であり、各 register の owner を一つに限定して reset/flush/stall/update/hold の優先順位を明示
- valid/payload、FIFO pointer/count、request fields など同じ transaction の状態は同じ更新規則で扱う
- clock/reset type と `if_reset` を使い、極性・同期性を設定と契約で管理
- reset は既知値が必要な state に限定し、memory array や valid=0 中に参照しない payload には付けない
- clock-domain annotation と `unsafe (cdc)` は CDC 回路を生成しないため、synchronizer、handshake、async FIFO などを実装
- interface、FIFO、memory は transfer 条件、backpressure、latency、read-during-write、同時操作、inference 条件を実装前に確定

## Verification and generated RTL

- comb function、sequential primitive、FIFO/RAM、protocol adapter、subsystem、top の順に小さく検証
- module boundary に valid stability、full/empty、alignment、one-hot、illegal opcode、grant exclusion などの contract assertion を配置
- signed arithmetic、X/Z、memory read-during-write、generated clock、async reset、simulator 依存処理は reference model または system-level test でも cross-check
- 下流 EDA の行番号は source map で Veryl へ戻し、toolchain 更新時は生成 RTL、filelist、module hierarchy の diff を確認
- `veryl synth` は設計探索の概算として扱い、vendor synthesis、place-and-route、timing sign-off の代替にしない
- FPGA では vendor primitive を wrapper へ隔離し、合成後に BRAM、DSP、carry、LUT などの inference report を確認
