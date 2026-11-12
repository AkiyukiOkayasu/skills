# Skills

OpenCode / Codex から読み込む個人用 skill。Paseo 管理の `paseo*` と外部 skill の `frontend-design` はここでは管理しない。

## 方針

- モデルが一般知識として持っていることは書かない。
- project 固有の規約、実機でしか分からない挙動、再現に手間がかかる手順だけを残す。
- 試行錯誤の履歴、変更履歴、アンチパターン集は書かない。
- 複数 skill で使う規則は `~/.agents/AGENTS.md` を正とし、skill では判断に必要な最小限だけ再掲する。
- reference は必要時にだけ読む。SKILL.md には判断に必要な結論だけを置く。

## 一覧

| Skill | 役割 |
|---|---|
| comment-review | コメントレビューの基準 |
| gndless-git | ブランチ名と日本語コミット |
| gndless-gowin | Gowin Tcl、gprj 同期、合成・PnR の制約 |
| gndless-ngspice | 単体 ngspice のバッチ解析と WAV 出力 |
| gndless-pdf | PDF の部分抽出・画像化 |
| gndless-release | リリース手順 |
| gndless-rust | Rust の doc comment、cargo、組み込み profile |
| gndless-veryl | Veryl の workflow、doc、cast、生成 RTL |
| gndless-click-detect | 1kHz サイン録音のクリック検出 |
| gndless-kicad-schematic | KiCad 回路図のシンボル、RKM、電源、ページ、ERC |
| gndless-kicad-pcb | 4層スタックアップ、配置、配線、USB2/PDM |
| gndless-kicad-fab | BOM、JLCPCB/Akizuki、組立フィールド |
| gndless-kicad-review | KiCad 全体レビュー、kicad/spice/datasheets の統括 |
| plan-workflow | plan/*.md の運用と risk 別レビュー |

## 外部 KiCad skill

`~/.local/share/kicad-agent-skills/install.sh` で 3 パックを導入する。Codex と OpenCode はどちらも `~/.agents/skills` を読む。

| パック | 由来 | 主な ID |
|---|---|---|
| kicad-happy | aklofas/kicad-happy | `kicad`, `bom`, `jlcpcb`, `lcsc`, `spice`, `datasheets` |
| Ki-Stack | Milind220/Ki-Stack | `ki-stack-file-surgery`, `ki-stack-symbols`, `ki-stack-footprints` |
| KiCadRoutingTools | drandyhaas/KiCadRoutingTools | `recommend-stackup`, `recommend-plane-mappings`, `analyze-power-nets`, `identify-diff-pairs`, `find-high-speed-nets`, `plan-pcb-placement`, `plan-pcb-routing`, `review-routed-board`, `diagnose-routing-failures` |

- 個人規約は `gndless-kicad-schematic` / `gndless-kicad-pcb` / `gndless-kicad-fab` / `gndless-kicad-review` の工程別 skill。解析用の `kicad` は kicad-happy の core で、別物。
- American-Embedded は削除した。`digikey` / `mouser` / `element14` / `pcbway` / `emc`、書き出し・レンダー系、Ki-Stack の live 系は削除済み。KRT の解析系は4層・USB2・差動PDM向けに戻した。
- どの skill をどの用途で使うか、矛盾点と優先順位は `gndless-kicad-review/references/third-party-routing.md` にまとめている。
- kicad-happy、Ki-Stack、KiCadRoutingTools は絶対パスへ書き換えた copy。
- Python 依存は `~/.local/share/kicad-agent-skills/venv` に導入済み。
- `kicad-cli` は KiCad 10、`kicad-cli9` は KiCad 9 を `~/.local/bin` に symlink している。
- `kikit` は削除済み。`kiutils-inspect` は Rust build を使う。
- 更新は `~/.local/share/kicad-agent-skills/install.sh` を実行する。

## 管理外

- `paseo*`: Paseo が生成・管理する。
- `frontend-design`: 外部 skill (gitignore)。
- `tmp/`: gndless-pdf などの出力。
