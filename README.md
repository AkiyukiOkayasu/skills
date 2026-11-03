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
| kicad | KiCad の部品 field、値表記、配置、検証 |
| plan-workflow | plan/*.md の運用と risk 別レビュー |

## 管理外

- `paseo*`: Paseo が生成・管理する。
- `frontend-design`: 外部 skill (gitignore)。
- `tmp/`: gndless-pdf などの出力。
