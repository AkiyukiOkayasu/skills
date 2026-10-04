---
name: gndless-gowin
description: Use when working on Gowin-specific project automation and device caveats, including Tcl scripts, gw_sh flows, generated RTL import, project bring-up, and board-specific behaviors not obvious from Gowin documentation.
---

# Gndless Gowin

Gowin EDA の Tcl スクリプト、project automation、device 依存の注意点。

## 基本方針

- Tcl は IDE のカレントディレクトリに依存させず、script 相対で書く
- 生成元は Veryl、合成入口は Gowin project、という責務分離を保つ
- 人手 GUI 操作だけに閉じた手順を残さない
- Gowin document に無い不安定要因や undocumented behavior は、再発防止のため skill に残す

## Tcl script の要点

- `set script_path [file normalize [info script]]` と `set script_dir [file dirname $script_path]` を先頭で定義する
- project path と file list は `file join` で `script_dir` から組み立てる
- `open_project` 後に `set_option` を明示する (gprj に残った設定に依存しない)
- `import_files -fileList ... -force` で最新の生成物を再投入する
- `run all` と `run close` まで含めて自動化する。`run close` で gprj に変更が保存される (`run all` だけでは保存されない)

## gw_sh の実行

- `./gw_sh run_gowin_example.tcl` のように Tcl script を渡して実行する
- Gowin IDE の絶対パス解決、`DYLD_LIBRARY_PATH` など実行環境の注入、project ごとの複合 build フローは Tcl の外側 (wrapper script、just など) で扱う
- Tcl 側は「project をどう開いて何を設定するか」に集中させ、`cd` 前提の相対パスや環境依存を持ち込まない

## Gowin 合成の既知制約: interface 配列の procedural for

Gowin Synthesis は、`always_ff` / `always_comb` 内の `for` ループで interface (modport) 配列要素を変数インデックス選択できない (Veryl の interface が生成する SV の配列要素アクセスが定数展開されない)。

- エラー例: `ERROR (EX3812) : 'i' is not a constant`
- 定数インデックス (`channels[0].raw` など) は合成できる。問題になるのは変数 `i` を使うループだけ
- この制約は `veryl check` / `veryl test` では検出されず、Gowin 合成でのみ失敗する

回避パターン (Veryl): 入力 interface は generate assign で raw の plain 配列へ展開し、procedural 内は plain 配列を扱う。出力も plain 配列から generate assign で接続する。testbench (合成対象外) の `.raw` アクセスには適用不要。

```veryl
var i_channels_raw: gndless_fixedpoint::Q1_23::Raw [8];
for i in 0..8 :g_ich {
    assign i_channels_raw[i] = i_channels[i].raw;
}

for i in 0..8 :g_out {
    assign o_channels[i].raw = o_channels_raw[i];
}
```

## PnR 配置・ルーティングオプション

タイミングマージンが足りないとき、合成オプションで改善しない場合は、PnR の配置・ルーティングアルゴリズム選択を試す。

- `-place_option 2`: timing 優先の配置。単独で改善することが多い
- `-place_option 3` / `4`: 複数試行から最良を選択 (詳細は未公開)
- `-route_option 1`: timing に従うルーティング
- 実測では `-place_option 3` + `-route_option 1` が最良 (FPGA_Oscillator で Fmax 50.4 → 62.6 MHz)
- PnR 設定は `impl/pnr/cmd.do` に保存され、option 変更が反映されないことがある。`set_option` を変えたら `impl/pnr/cmd.do` を削除して再実行する

Option 定義、実測、測定の作法は [references/pnr-placement-options.md](references/pnr-placement-options.md)。

## 設定の確認と no-op option

現在の全設定を dump して、合成 script の `set_option` 漏れを洗い出すには `saveto -all_options` を使う。

```tcl
open_project myProject/myProject.gprj
saveto -all_options project_config.tcl
run close
```

- `-retiming` / `-pipe` は headless `gw_sh` フローでは no-op (V1.9.12 で検証)。`saveto -all_options`、gprj、合成 `.prj`、公式 Tcl ガイド (SUG1220) のどこにも現れず、`set_option` で設定しても合成ネットリストが変化しないため tcl から削除してよい
- `-route_maxfan` は PnR の `cmd.do` に現れる実オプションなので残す

## project の作成と合成

- 新規 project: [create_project_example.tcl](create_project_example.tcl) をテンプレートに `device` / `top` / `file list` / `pin option` を実プロジェクトへ合わせる
- 既存 project の合成: [run_gowin_example.tcl](run_gowin_example.tcl) をベースに `project_path` / `filelist_path` / `top module` / `pin option` を合わせる
- GUI で gprj を作った場合も、`saveto -all_options` で設定を書き出して script のベースにする
- `create_project` の構文: `create_project -name <prjName> -dir <path> -pn <pnName> [-device_version <arg>] [-force]`

## project 新設時の確認項目

- device が正しいか
- top module 名が一致しているか
- `import_files` の file list が最新の生成物を向いているか
- `saveto -all_options` で設定漏れを確認したか

### JTAG / 特殊 pin

- JTAG / READY / CPU / MSPI など Multi-purpose pin option が用途に合っているか
- ベースは `create_project_example.tcl` の multi-purpose pins 節。実機の書き込み・起動経路と突き合わせる

### MultiBoot

- MultiBoot を使うなら address 幅と flash address が正しいか (`-multi_boot` / `-mspi_jump`)

### Bitstream

- `-bit_format` / `-bit_security` / `-bit_incl_bsram_init` / `-loading_rate` を用途に合わせる

### BSRAM / boot / reset

- BSRAM や boot 周辺の安定化に reset delay が必要か
- Background programming (`-bg_programming`) が必要か
- reset 方針を変えるなら、実機起動確認なしに削らない
- document に見当たらないからといって、実機で必要だった reset / boot 対策を消さない

## アンチパターン

- `cd` 前提の相対パスで script を書く
- GUI で設定しただけで Tcl に落とさない
- `impl/` 配下の成果物を入力ソースとして扱う
- `run all` で必要になる file list 更新を忘れる
- device 固有 option を説明なしにコピペする
- document に見当たらない挙動だからといって、実機で必要だった reset / boot 対策を消す
