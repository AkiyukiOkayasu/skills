---
name: gndless-veryl
description: Use when editing Veryl RTL, including workflow, doc comments, naming, casts, and generated-RTL checks.
---

# Gndless Veryl

## 基本

- `.veryl` を正とし、`target/` などの生成 `.sv`、`.sv.map`、`.f` は直接編集しない
- `Veryl.toml`、toolchain、下流 build script、project 固有 skill を先に確認する
- board、register map、Fmax、vendor flow は project 側を優先する

## Workflow

`.veryl` を変更したら対象 project で次を実行する。

```text
veryl fmt
veryl check
veryl test
veryl build
```

- 小さな unit test と native test を優先し、長い test は必要時だけ `veryl test --ignored`
- backend 差は `veryl test --backend-validate`、`--wave` は失敗再現・波形解析時だけ使う
- system-level の性質だけ project 側の外部 simulation を併用する
- `Veryl.toml` の `version`、`Veryl.lock`、`Veryl.pub` は手動で編集しない。バージョン更新と publish は `veryl publish --bump` に任せる
- migration、dependency update、publish は [references/publishing.md](references/publishing.md) を読む

## Documentation comments

- 公開 module、interface、function、型、port、parameter、const の契約を書く
- 形式は [references/documentation.md](references/documentation.md) に従う
- Mermaid と WaveDrom を積極的に使い、可能なら `wavedrom,test` を優先する

## Naming and types

- project の既存規約を優先する。無ければ file/function/local/instance/port は `snake_case`、public module/interface は `UpperCamelCase`、param/const は `UPPER_SNAKE_CASE`、package は `PascalCase`
- port は方向 prefix/suffix ではなく意味名を使い、clock は `clk`、system reset は `rst`
- public port、module 契約、register/accumulator の width、signedness が重要な境界では型を明示する
- FSM は enum、関連する pipeline/bus signal は struct を検討し、public transaction と internal transaction を分離する
- width 変更は `$std::zero_extend` / `$std::one_extend` / `$std::sign_extend` / `$std::truncate` を優先する。cast の詳細は [references/casting.md](references/casting.md)
- generic、Boolean type、packed/unpacked は [references/language-notes.md](references/language-notes.md) を読む

## RTL design

- `always_comb` は output/next-state を先頭で default assignment し、全経路で代入する
- `always_ff` の `=` は nonblocking 相当。各 register の owner を1つに限定し、reset/flush/stall/update/hold の優先順位を明示する
- valid/payload、FIFO pointer/count、request fields など同じ transaction の状態は同じ更新規則で扱う
- clock/reset type と `if_reset` を使い、極性・同期性を設定と契約で管理する
- reset は既知値が必要な state に限定し、memory array や valid=0 中に参照しない payload には付けない
- clock-domain annotation と `unsafe (cdc)` は CDC 回路を生成しない。synchronizer、handshake、async FIFO を実装する
- interface、FIFO、memory は transfer 条件、backpressure、latency、read-during-write、同時操作、inference 条件を実装前に確定する

## Verification

- module boundary に valid stability、full/empty、alignment、one-hot、illegal opcode、grant exclusion などの assertion を置く
- 下流 EDA の行番号は source map で Veryl へ戻す。toolchain 更新時は生成 RTL、filelist、module hierarchy の diff を確認する
- `veryl synth` は設計探索の概算で、vendor synthesis、PnR、timing sign-off の代替にしない
- FPGA では vendor primitive を wrapper へ隔離し、合成後に BRAM、DSP、carry、LUT の inference report を確認する
